# app.py
# ==============================================================================
# A comprehensive Streamlit application for personal library management.
#
# Features:
# - Dashboard with detailed reading statistics and progress visualization.
# - Daily reading logger.
# - A digital bookshelf to view the entire collection.
# - Search functionality for titles, authors, and genres.
# - Secure admin panel for managing the library collection.
#   - Add new books.
#   - Edit existing book details.
#   - Delete books with confirmation.
# - Data export functionality for both the library and reading logs.
#
# Author: Sourab (with enhancements by Gemini)
# ==============================================================================

# --- IMPORT LIBRARIES ---
import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from datetime import date

# --- PAGE CONFIGURATION ---
# Sets the configuration for the Streamlit page. This should be the first Streamlit command.
st.set_page_config(
    page_title="Finoptiv Library",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
def load_css(file_name):
    """
    Loads a CSS file and injects it into the Streamlit app.
    If the file is not found, it provides default styles for graceful fallback.
    """
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file not found: '{file_name}'. Using default styles. For custom styling, create a 'style.css' file.")
        # Default styles to ensure the app is presentable without the external CSS file.
        st.markdown("""
        <style>
            .sidebar-header { font-size: 24px; font-weight: bold; color: #013237; padding: 10px; text-align: center; }
            .sidebar-hr { border-top: 1px solid #C0E6BA; }
            .sidebar-footer { font-size: 12px; text-align: center; color: grey; padding-top: 20px; }
            .book-card { background-color: #FFFFFF; border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); transition: transform 0.2s; height: 180px; display: flex; flex-direction: column; justify-content: space-between; }
            .book-card:hover { transform: scale(1.02); }
            .book-card-header { font-size: 18px; font-weight: bold; color: #013237; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .book-card-author { font-size: 14px; color: #555; margin-bottom: 10px; }
            .book-card-details { font-size: 12px; color: #777; }
        </style>
        """, unsafe_allow_html=True)

load_css("style.css")

# --- DATA MANAGEMENT & SECURITY ---
LIBRARY_FILE = 'library.csv'
LOG_FILE = 'daily_log.csv'
ADMIN_PASSWORD = "23030127"  # IMPORTANT: In a real-world app, use st.secrets for this.

def load_data(file_path, columns):
    """
    Loads data from a CSV file. If the file doesn't exist or is empty,
    it returns an empty DataFrame with the specified columns.
    """
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(columns=columns)
    # Ensure all required columns exist, adding them if necessary.
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df

def save_data(df, file_path):
    """Saves a DataFrame to a CSV file."""
    df.to_csv(file_path, index=False)

@st.cache_data
def convert_df_to_csv(df):
    """
    Converts a Pandas DataFrame to a CSV string, optimized with Streamlit's cache.
    """
    return df.to_csv(index=False).encode('utf-8')

# --- SESSION STATE INITIALIZATION ---
# Using st.session_state to persist data across reruns.
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
    
    # Dynamically adjust navigation options based on admin login status.
    options = ["Dashboard", "Library", "Search"]
    icons = ["bar-chart-line-fill", "book-half", "search"]
    if st.session_state.admin_access:
        options.insert(1, "Admin Panel")
        icons.insert(1, "shield-lock-fill")

    page = option_menu(
        menu_title=None,
        options=options,
        icons=icons,
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#4CA771", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#EAF9E7", "color": "#013237"},
            "nav-link-selected": {"background-color": "#C0E6BA", "color": "#013237"},
        }
    )
    
    st.markdown("<hr class='sidebar-hr'>", unsafe_allow_html=True)
    
    # Admin Login/Logout Section
    if not st.session_state.admin_access:
        with st.expander("🔑 Admin Login"):
            password = st.text_input("Password", type="password", key="admin_password")
            if st.button("Login", key="login_button"):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_access = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
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
        """, unsafe_allow_html=True
    )

# --- PAGE RENDERING LOGIC ---

# 1. Dashboard Page
if page == "Dashboard":
    st.title("📊 Finoptiv Books Dashboard")
    st.markdown("Your personal reading command center. Track progress, log entries, and stay motivated.")
    st.markdown("---")

    # Key Performance Indicators (KPIs)
    if not st.session_state.library_df.empty:
        total_books = len(st.session_state.library_df)
        read_books = len(st.session_state.library_df[st.session_state.library_df['Status'] == 'Read'])
        total_pages_read_log = st.session_state.log_df['Pages Read'].sum() if not st.session_state.log_df.empty else 0
        total_time_spent_log = st.session_state.log_df['Time Spent (min)'].sum() if not st.session_state.log_df.empty else 0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1: st.metric(label="Total Books 📖", value=total_books)
        with kpi2: st.metric(label="Books Read ✅", value=f"{read_books} ({read_books/total_books:.1%})")
        with kpi3: st.metric(label="Total Pages Read 📄", value=f"{int(total_pages_read_log):,}")
        with kpi4: st.metric(label="Total Reading Time 🕒", value=f"{total_time_spent_log / 60:.1f} hours")
    else:
        st.info("Start by adding books and logging your reading to see your stats here!")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Reading Progress")
        if not st.session_state.library_df.empty:
            progress = (read_books / total_books) * 100
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=progress,
                title={'text': f"<b>{read_books} of {total_books} Books Completed</b>", 'font': {'size': 20, 'color': '#013237'}},
                gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#4CA771"}, 'steps': [{'range': [0, 100], 'color': '#EAF9E7'}]},
            ))
            fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)
        else:
            st.info("Add books to see your progress.")
    
    with col2:
        st.subheader("Top Genres")
        if not st.session_state.library_df.empty:
            genre_counts = st.session_state.library_df['Genre'].value_counts().nlargest(5)
            fig_pie = go.Figure(data=[go.Pie(labels=genre_counts.index, values=genre_counts.values, hole=.4,
                                             marker_colors=['#4CA771', '#C0E6BA', '#F8B14D', '#F46A9B', '#9C34E3'])])
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Your genre summary will appear here.")

    st.markdown("---")
    st.subheader("Log Today's Reading")
    if not st.session_state.library_df.empty:
        with st.form("multi_log_form"):
            for i, entry in enumerate(st.session_state.reading_log_entries):
                cols = st.columns([3, 1, 1])
                entry['book'] = cols[0].selectbox("Book Title", st.session_state.library_df['Title'].unique(), key=f"book_{i}")
                entry['pages'] = cols[1].number_input("Pages", min_value=1, step=1, key=f"pages_{i}")
                entry['time'] = cols[2].number_input("Mins", min_value=1, step=1, key=f"time_{i}")
            
            col_add, col_submit = st.columns([1, 5])
            if col_add.form_submit_button("Add Another"):
                st.session_state.reading_log_entries.append({"book": "", "pages": 1, "time": 1})
                st.rerun()
            
            if col_submit.form_submit_button("Submit All Log Entries"):
                for entry in st.session_state.reading_log_entries:
                    new_log_entry = pd.DataFrame([{"Date": str(date.today()), "Book Title": entry['book'], "Pages Read": entry['pages'], "Time Spent (min)": entry['time']}])
                    st.session_state.log_df = pd.concat([st.session_state.log_df, new_log_entry], ignore_index=True)
                save_data(st.session_state.log_df, LOG_FILE)
                st.session_state.reading_log_entries = [{"book": "", "pages": 1, "time": 1}] 
                st.success("Successfully logged all reading entries!")
                st.rerun()
    else:
        st.warning("You must add books to your library before you can log your reading.")

# 2. Admin Panel Page (Admin Only)
elif page == "Admin Panel":
    st.header("🔑 Admin Panel")
    st.markdown("Manage your library's collection: add, edit, delete, and export data.")

    tab1, tab2, tab3 = st.tabs(["📚 Manage Books", "➕ Add New Book", "📤 Data Export"])

    # --- Manage Books Tab ---
    with tab1:
        st.subheader("Edit or Delete Existing Books")
        if not st.session_state.library_df.empty:
            for index, row in st.session_state.library_df.iterrows():
                st.markdown("---")
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.markdown(f"**{row['Title']}** by {row['Author']}")
                    st.caption(f"Genre: {row['Genre']} | Pages: {row['Pages']} | Status: {row['Status']}")

                with col2:
                    with st.expander("📝 Edit"):
                        with st.form(key=f"edit_form_{index}"):
                            new_title = st.text_input("Title", value=row['Title'], key=f"title_{index}")
                            new_author = st.text_input("Author", value=row['Author'], key=f"author_{index}")
                            new_genre = st.text_input("Genre", value=row['Genre'], key=f"genre_{index}")
                            new_pages = st.number_input("Pages", value=row['Pages'], min_value=1, step=1, key=f"pages_edit_{index}")
                            status_options = ["Not Started", "Reading", "Read"]
                            current_status_index = status_options.index(row['Status']) if row['Status'] in status_options else 0
                            new_status = st.selectbox("Status", options=status_options, index=current_status_index, key=f"status_edit_{index}")

                            if st.form_submit_button("Save Changes"):
                                st.session_state.library_df.loc[index] = [new_title, new_author, new_genre, new_pages, new_status]
                                save_data(st.session_state.library_df, LIBRARY_FILE)
                                st.success(f"Book '{new_title}' updated successfully!")
                                st.rerun()
                
                with col3:
                    with st.expander("🗑️ Delete"):
                        st.warning(f"Delete '{row['Title']}'?")
                        if st.button("Confirm Delete", key=f"confirm_delete_{index}", type="primary"):
                            st.session_state.library_df = st.session_state.library_df.drop(index).reset_index(drop=True)
                            save_data(st.session_state.library_df, LIBRARY_FILE)
                            st.success(f"Book '{row['Title']}' has been permanently deleted.")
                            st.rerun()
        else:
            st.info("The library is empty. Add books using the 'Add New Book' tab.")

    # --- Add New Book Tab ---
    with tab2:
        st.subheader("Add a New Book to the Library")
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
                else:
                    st.error("❌ Please fill in all fields.")

    # --- Data Export Tab ---
    with tab3:
        st.subheader("Export Library Data")
        st.markdown("Download your library or reading log data as a CSV file.")
        
        st.markdown("#### Library Collection")
        st.download_button(
            label="Download library.csv",
            data=convert_df_to_csv(st.session_state.library_df),
            file_name='library_collection.csv', mime='text/csv'
        )

        st.markdown("#### Reading Log")
        st.download_button(
            label="Download daily_log.csv",
            data=convert_df_to_csv(st.session_state.log_df),
            file_name='reading_log.csv', mime='text/csv'
        )

# 3. Library Page
elif page == "Library":
    st.header("Your Digital Bookshelf")
    if not st.session_state.library_df.empty:
        num_columns = 3
        cols = st.columns(num_columns)
        
        for index, row in st.session_state.library_df.iterrows():
            with cols[index % num_columns]:
                with st.container():
                    st.markdown(f"""
                    <div class="book-card">
                        <div>
                            <div class="book-card-header" title="{row['Title']}">{row['Title']}</div>
                            <div class="book-card-author">by {row['Author']}</div>
                            <div class="book-card-details">{row['Genre']} | {row['Pages']} pages</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    status_options = ["Read", "Reading", "Not Started"]
                    current_status_index = status_options.index(row['Status']) if row['Status'] in status_options else 2
                    
                    new_status = st.selectbox(
                        "Update Status", options=status_options, index=current_status_index,
                        key=f"status_lib_{index}", label_visibility="collapsed"
                    )

                    if new_status != row['Status']:
                        st.session_state.library_df.loc[index, 'Status'] = new_status
                        save_data(st.session_state.library_df, LIBRARY_FILE)
                        st.rerun()
    else: 
        st.info("Your library is empty. An admin must add books to start your collection!")

# 4. Search Page
elif page == "Search":
    st.header("Find a Book in Your Library")
    search_query = st.text_input("", placeholder="Search by Title, Author, or Genre...", label_visibility="collapsed")
    if search_query:
        query = search_query.lower()
        results_df = st.session_state.library_df[
            st.session_state.library_df['Title'].str.lower().str.contains(query, na=False) |
            st.session_state.library_df['Author'].str.lower().str.contains(query, na=False) |
            st.session_state.library_df['Genre'].str.lower().str.contains(query, na=False)
        ]
        st.markdown(f"Found **{len(results_df)}** matching books.")
        if not results_df.empty:
            st.dataframe(results_df, use_container_width=True, hide_index=True)
    else:
        st.info("Enter a search term to find books in your library.")
