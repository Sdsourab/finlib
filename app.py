# app.py
import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
from datetime import date
import io
import plotly.graph_objects as go
import plotly.express as px


# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Finoptiv Library",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
def local_css(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file not found: {file_name}. Make sure 'style.css' is in the same directory.")

local_css("style.css")

# --- DATA MANAGEMENT & SECURITY ---
LIBRARY_FILE = 'library.csv'
LOG_FILE = 'daily_log.csv'
ADMIN_PASSWORD = "23030127" # Highly confidential

def load_data(file_path, columns):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(columns=columns)
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# --- SESSION STATE INITIALIZATION ---
if 'library_df' not in st.session_state:
    st.session_state.library_df = load_data(LIBRARY_FILE, ["Title", "Author", "Genre", "Pages", "Status"])
if 'log_df' not in st.session_state:
    st.session_state.log_df = load_data(LOG_FILE, ["Date", "Book Title", "Pages Read", "Time Spent (min)"])
if 'admin_access' not in st.session_state:
    st.session_state.admin_access = False
if 'reading_log_entries' not in st.session_state:
    st.session_state.reading_log_entries = [{"book": "", "pages": 1, "time": 1}]

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<div class='sidebar-header'>Finoptiv Library</div>", unsafe_allow_html=True)
    options = ["Dashboard", "Library", "Search"]
    icons = ["bar-chart-line-fill", "book-half", "search"]
    if st.session_state.admin_access:
        options.insert(1, "Add Book")
        icons.insert(1, "plus-circle-fill")

    page = option_menu(menu_title=None, options=options, icons=icons, menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#4CA771", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#EAF9E7", "color": "#013237"},
            "nav-link-selected": {"background-color": "#C0E6BA", "color": "#013237"},
        })
    st.markdown("<hr class='sidebar-hr'>", unsafe_allow_html=True)
    if not st.session_state.admin_access:
        with st.expander("Admin Login"):
            password = st.text_input("Password", type="password", key="admin_password")
            if st.button("Login", key="login_button"):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_access = True
                    st.rerun()
                else: st.error("Incorrect password")
    else:
        if st.button("Logout from Admin"):
            st.session_state.admin_access = False
            st.rerun()
    st.markdown("<hr class='sidebar-hr'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='sidebar-footer'>
            Developed by <b>Sourab</b><br>
            <a href="https://finoptiv.vercel.app" target="_blank">finoptiv.vercel.app</a>
        </div>
        """, unsafe_allow_html=True)

# --- PAGE RENDERING LOGIC ---

# 1. Dashboard Page
if page == "Dashboard":
    st.title("Finoptiv Books")
    st.markdown("Time to relax and read a book.")
    st.markdown("---")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Your Reading Progress")
        total_books = len(st.session_state.library_df)
        if total_books > 0:
            read_books = len(st.session_state.library_df[st.session_state.library_df['Status'] == 'Read'])
            progress = (read_books / total_books) * 100 if total_books > 0 else 0
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = progress,
                title = {'text': f"<b>{read_books} of {total_books} Books Completed</b>", 'font': {'size': 20, 'color': '#013237'}},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "#4CA771"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "#EAEAEA",
                    'steps': [
                        {'range': [0, 100], 'color': '#EAF9E7'}],
                },
                number={'font': {'color': '#013237'}}
                ))
            fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)
        else:
            st.info("Add books to your library to see your progress.")
    
    with col2:
        st.subheader("Library Summary")
        if not st.session_state.library_df.empty:
            genre_counts = st.session_state.library_df['Genre'].value_counts().nlargest(5)
            
            x_data = genre_counts.index
            y_data = genre_counts.values
            bar_colors = ['#F8B14D', '#F46A9B', '#EC44C3', '#9C34E3', '#6A23D9']
            
            # --- MATPLOTLIB IMPLEMENTATION (FIXED) ---
            fig, ax = plt.subplots(figsize=(8, 5))
            fig.patch.set_alpha(0.0) # Transparent background for the figure
            ax.set_facecolor('none') # Transparent background for the axes

            ax.bar(x_data, y_data, color=bar_colors[:len(x_data)], width=0.6)
            ax.plot(x_data, y_data, color='lightgrey', marker='o', markersize=8,
                    markerfacecolor='white', markeredgecolor='grey', linewidth=2)
            
            for i, val in enumerate(y_data):
                ax.plot(x_data[i], val, marker='o', markersize=5, color=bar_colors[i])
                ax.text(i, val + 0.1, f"+{val}", ha='center', va='bottom', fontsize=12, color='#333')

            ax.set_title("BAR GRAPH", fontsize=14, weight='bold', color='#555')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_color('lightgrey')
            
            ax.tick_params(axis='x', colors='grey')
            ax.tick_params(axis='y', colors='grey')
            ax.yaxis.grid(True, linestyle='--', which='major', color='lightgrey', alpha=0.7)
            ax.set_yticks([])

            plt.tight_layout()
            st.pyplot(fig, facecolor='none')
            # --- END OF MATPLOTLIB IMPLEMENTATION ---

        else:
            st.info("Your genre summary will appear here.")


    st.markdown("---")
    st.subheader("Daily Report")
    today_log = st.session_state.log_df[st.session_state.log_df['Date'] == str(date.today())]
    if not today_log.empty:
        report_data = today_log.groupby('Book Title').agg({'Pages Read': 'sum', 'Time Spent (min)': 'sum'}).reset_index()
        
        fig_daily = go.Figure()
        fig_daily.add_trace(go.Bar(
            x=report_data['Book Title'], y=report_data['Pages Read'], name='Pages Read',
            marker_color='#4CA771', marker_line_color='white', marker_line_width=1.5, width=0.4
        ))
        fig_daily.add_trace(go.Bar(
            x=report_data['Book Title'], y=report_data['Time Spent (min)'], name='Time Spent (min)',
            marker_color='#C0E6BA', marker_line_color='white', marker_line_width=1.5, width=0.4
        ))
        fig_daily.update_layout(
            barmode='group', title_text="Today's Reading Activity", xaxis_title="Book Title", yaxis_title="Total",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend_title_text='Metric', bargap=0.2, bargroupgap=0.1,
            font_color='#013237'
        )
        st.plotly_chart(fig_daily, use_container_width=True)

        img_bytes = fig_daily.to_image(format="jpeg", width=1000, height=600, scale=2)
        st.download_button(label="Download Daily Report Graph", data=img_bytes, file_name="daily_report.jpeg", mime="image/jpeg")
    else:
        st.info("No reading logged for today. Your daily report will appear here.")

# 2. Add Book Page (Admin Only)
elif page == "Add Book":
    st.header("Admin Panel: Add a New Book")
    with st.form("new_book_form", clear_on_submit=True):
        title = st.text_input("Book Title", placeholder="e.g., The Silent Patient")
        author = st.text_input("Author Name", placeholder="e.g., Alex Michaelides")
        genre = st.text_input("Genre", placeholder="e.g., Thriller")
        col1, col2 = st.columns(2)
        with col1: pages = st.number_input("Total Pages", min_value=1, step=1)
        with col2: status = st.selectbox("Reading Status", ["Not Started", "Reading", "Read"])
        if st.form_submit_button("Add Book to Library"):
            if title and author and pages and genre:
                new_book = pd.DataFrame([{"Title": title, "Author": author, "Genre": genre, "Pages": pages, "Status": status}])
                st.session_state.library_df = pd.concat([st.session_state.library_df, new_book], ignore_index=True)
                save_data(st.session_state.library_df, LIBRARY_FILE)
                st.success(f"✅ Book '{title}' added successfully!")
            else: st.error("❌ Please fill in all fields.")

# 3. Library Page
elif page == "Library":
    st.header("Your Digital Bookshelf")
    if not st.session_state.library_df.empty:
        num_columns = 3
        cols = st.columns(num_columns)
        
        df_copy = st.session_state.library_df.copy()

        for index, row in df_copy.iterrows():
            with cols[index % num_columns]:
                with st.container():
                    st.markdown(f"""
                    <div class="book-card" style="height: 160px; margin-bottom: 5px;">
                        <div class="book-card-header">{row['Title']}</div>
                        <div class="book-card-author">by {row['Author']}</div>
                        <div class="book-card-details">{row['Genre']} | {row['Pages']} pages</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    status_options = ["Read", "Reading", "Not Started"]
                    current_status_index = status_options.index(row['Status']) if row['Status'] in status_options else 2
                    
                    new_status = st.selectbox(
                        "Status",
                        options=status_options,
                        index=current_status_index,
                        key=f"status_{index}",
                        label_visibility="collapsed"
                    )

                    if new_status != row['Status']:
                        st.session_state.library_df.loc[index, 'Status'] = new_status
                        save_data(st.session_state.library_df, LIBRARY_FILE)
                        st.rerun()
    else: 
        st.info("Your library is empty. An admin must add books to start your collection!")


# 4. Search Page
elif page == "Search":
    st.header("Find a Book")
    search_query = st.text_input("", placeholder="Search by Title, Author, or Genre...", label_visibility="collapsed")
    if search_query:
        query = search_query.lower()
        results_df = st.session_state.library_df[
            st.session_state.library_df['Title'].str.lower().str.contains(query) |
            st.session_state.library_df['Author'].str.lower().str.contains(query) |
            st.session_state.library_df['Genre'].str.lower().str.contains(query)]
        st.markdown(f"Found **{len(results_df)}** matching books.")
        if not results_df.empty:
            st.dataframe(results_df, use_container_width=True, hide_index=True)
    else: st.info("Enter a search term to find books in your library.")
