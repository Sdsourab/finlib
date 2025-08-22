# app.py
import streamlit as st
import pandas as pd
import os
from streamlit_option_menu import option_menu
from datetime import date
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
# Sets the basic configuration for the Streamlit page.
st.set_page_config(
    page_title="Finoptiv Library",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATA MANAGEMENT & SECURITY ---
LIBRARY_FILE = 'library.csv'
LOG_FILE = 'daily_log.csv'
ADMIN_PASSWORD = "admin123" # In a real-world app, use a more secure method like environment variables.

def load_data(file_path, columns):
    """
    Loads data from a CSV file. If the file doesn't exist or is empty,
    it creates a new DataFrame with the specified columns.
    """
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(columns=columns)
    # Ensure all required columns exist in the DataFrame.
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df

def save_data(df, file_path):
    """Saves a DataFrame to a CSV file, ensuring data integrity."""
    df.to_csv(file_path, index=False)

# --- SESSION STATE INITIALIZATION ---
# Using st.session_state to persist data across user interactions.
if 'library_df' not in st.session_state:
    st.session_state.library_df = load_data(LIBRARY_FILE, ["Title", "Author", "Genre", "Pages", "Status"])
if 'log_df' not in st.session_state:
    st.session_state.log_df = load_data(LOG_FILE, ["Date", "Book Title", "Pages Read", "Time Spent (min)"])
if 'admin_access' not in st.session_state:
    st.session_state.admin_access = False
if 'reading_log_entries' not in st.session_state:
    # This allows users to log multiple books at once.
    st.session_state.reading_log_entries = [{"book": "", "pages": 1, "time": 1}]

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #4CA771;'>Finoptiv Library</h1>", unsafe_allow_html=True)
    
    # Menu options change dynamically based on admin login status.
    options = ["Dashboard", "Library", "Search"]
    icons = ["bar-chart-line-fill", "book-half", "search"]
    if st.session_state.admin_access:
        options.insert(1, "Admin Panel")
        icons.insert(1, "shield-lock-fill")

    # The main navigation menu component.
    page = option_menu(
        menu_title=None, 
        options=options, 
        icons=icons, 
        menu_icon="cast", 
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#4CA771", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#EAF9E7", "color": "#013237"},
            "nav-link-selected": {"background-color": "#C0E6BA", "color": "#013237"},
        }
    )
    
    st.markdown("<hr style='border-color: #C0E6BA;'>", unsafe_allow_html=True)

    # Admin login/logout section.
    if not st.session_state.admin_access:
        with st.expander("Admin Login", expanded=False):
            password = st.text_input("Password", type="password", key="admin_password")
            if st.button("Login", key="login_button"):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_access = True
                    st.success("Admin access granted!")
                    st.rerun()
                else:
                    st.error("Incorrect password")
    else:
        if st.button("Logout from Admin"):
            st.session_state.admin_access = False
            st.rerun()
            
    st.markdown("<hr style='border-color: #C0E6BA;'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='text-align: center; padding: 10px; color: #013237;'>
            Developed by <b>Sourab</b><br>
            <a href="https://finoptiv.vercel.app" target="_blank" style='color: #4CA771;'>finoptiv.vercel.app</a>
        </div>
        """, unsafe_allow_html=True)

# --- PAGE RENDERING LOGIC ---

# 1. Dashboard Page (Accessible to all users)
if page == "Dashboard":
    st.title("📚 Finoptiv Books")
    st.markdown("Time to relax and read a book.")
    st.markdown("---")

    # Section for any user to log their reading for the day.
    st.subheader("Log Today's Reading")
    if not st.session_state.library_df.empty:
        with st.form("multi_log_form"):
            # Dynamically create form fields for each book entry.
            for i, entry in enumerate(st.session_state.reading_log_entries):
                cols = st.columns([3, 1, 1])
                entry['book'] = cols[0].selectbox("Book Title", st.session_state.library_df['Title'].unique(), key=f"book_{i}")
                entry['pages'] = cols[1].number_input("Pages Read", min_value=1, step=1, key=f"pages_{i}")
                entry['time'] = cols[2].number_input("Time (Mins)", min_value=1, step=1, key=f"time_{i}")
            
            col_add, col_submit = st.columns([1, 5])
            if col_add.form_submit_button("Add Another"):
                st.session_state.reading_log_entries.append({"book": "", "pages": 1, "time": 1})
                st.rerun()
            
            if col_submit.form_submit_button("Submit All Logs"):
                for entry in st.session_state.reading_log_entries:
                    new_log_entry = pd.DataFrame([{"Date": str(date.today()), "Book Title": entry['book'], "Pages Read": entry['pages'], "Time Spent (min)": entry['time']}])
                    st.session_state.log_df = pd.concat([st.session_state.log_df, new_log_entry], ignore_index=True)
                save_data(st.session_state.log_df, LOG_FILE)
                st.session_state.reading_log_entries = [{"book": "", "pages": 1, "time": 1}] 
                st.success("Successfully logged all reading entries!")
                st.rerun()
    else:
        st.warning("The library is empty. An admin must add books before you can log your reading.")

    st.markdown("---")

    # Section for all users to view today's reading progress.
    st.subheader("Today's Reading Report")
    today_log = st.session_state.log_df[st.session_state.log_df['Date'] == str(date.today())]
    if not today_log.empty:
        # Aggregate data for books that were logged multiple times today.
        report_data = today_log.groupby('Book Title').agg({'Pages Read': 'sum', 'Time Spent (min)': 'sum'}).reset_index()
        
        st.markdown("Here's a summary of all reading activity logged today:")
        
        # Displaying both a chart and a table for detailed viewing.
        col_chart, col_table = st.columns(2)
        with col_chart:
            fig_daily = go.Figure()
            fig_daily.add_trace(go.Bar(
                x=report_data['Book Title'], y=report_data['Pages Read'], name='Pages Read',
                marker_color='#4CA771'
            ))
            fig_daily.add_trace(go.Bar(
                x=report_data['Book Title'], y=report_data['Time Spent (min)'], name='Time Spent (min)',
                marker_color='#C0E6BA'
            ))
            fig_daily.update_layout(
                barmode='group', title_text="Activity by Book", xaxis_title=None, yaxis_title="Total",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color='#013237', legend_title_text='Metric'
            )
            st.plotly_chart(fig_daily, use_container_width=True)
        
        with col_table:
            st.dataframe(report_data, use_container_width=True, hide_index=True)

    else:
        st.info("No reading has been logged for today. Your daily report will appear here once you log an entry.")


# 2. Admin Panel Page (Admin Only)
elif page == "Admin Panel":
    st.header("🛠️ Admin Panel: Manage Library")
    
    # Using tabs for a clean, organized admin interface.
    tab1, tab2, tab3 = st.tabs(["Add Book", "Edit Book", "Delete Book"])

    with tab1:
        st.subheader("Add a New Book")
        with st.form("new_book_form", clear_on_submit=True):
            title = st.text_input("Book Title", placeholder="e.g., The Silent Patient")
            author = st.text_input("Author Name", placeholder="e.g., Alex Michaelides")
            genre = st.text_input("Genre", placeholder="e.g., Thriller")
            pages = st.number_input("Total Pages", min_value=1, step=1)
            status = st.selectbox("Reading Status", ["Not Started", "Reading", "Read"])
            
            if st.form_submit_button("Add Book to Library"):
                if title and author and pages and genre:
                    if title in st.session_state.library_df['Title'].values:
                        st.error(f"A book with the title '{title}' already exists.")
                    else:
                        new_book = pd.DataFrame([{"Title": title, "Author": author, "Genre": genre, "Pages": pages, "Status": status}])
                        st.session_state.library_df = pd.concat([st.session_state.library_df, new_book], ignore_index=True)
                        save_data(st.session_state.library_df, LIBRARY_FILE)
                        st.success(f"✅ Book '{title}' added successfully!")
                else:
                    st.error("❌ Please fill in all fields.")

    with tab2:
        st.subheader("Edit an Existing Book")
        if not st.session_state.library_df.empty:
            book_to_edit_title = st.selectbox("Select a book to edit", options=st.session_state.library_df['Title'])
            
            if book_to_edit_title:
                book_index = st.session_state.library_df[st.session_state.library_df['Title'] == book_to_edit_title].index[0]
                book_data = st.session_state.library_df.loc[book_index]

                with st.form("edit_book_form"):
                    st.write(f"Editing details for: **{book_to_edit_title}**")
                    new_title = st.text_input("Book Title", value=book_data['Title'])
                    new_author = st.text_input("Author Name", value=book_data['Author'])
                    new_genre = st.text_input("Genre", value=book_data['Genre'])
                    new_pages = st.number_input("Total Pages", min_value=1, step=1, value=int(book_data['Pages']))
                    status_options = ["Not Started", "Reading", "Read"]
                    current_status_index = status_options.index(book_data['Status'])
                    new_status = st.selectbox("Reading Status", options=status_options, index=current_status_index)

                    if st.form_submit_button("Update Book"):
                        st.session_state.library_df.loc[book_index] = [new_title, new_author, new_genre, new_pages, new_status]
                        save_data(st.session_state.library_df, LIBRARY_FILE)
                        st.success(f"✅ Book '{new_title}' updated successfully!")
                        st.rerun()
        else:
            st.info("There are no books in the library to edit.")

    with tab3:
        st.subheader("Delete a Book")
        if not st.session_state.library_df.empty:
            book_to_delete_title = st.selectbox("Select a book to delete", options=st.session_state.library_df['Title'], key="delete_select")

            if book_to_delete_title:
                st.warning(f"**Warning:** You are about to delete **'{book_to_delete_title}'**. This action cannot be undone.")
                confirm_delete = st.checkbox("I understand and want to delete this book.")

                if st.button("Delete Book Permanently", disabled=not confirm_delete):
                    index_to_delete = st.session_state.library_df[st.session_state.library_df['Title'] == book_to_delete_title].index
                    st.session_state.library_df = st.session_state.library_df.drop(index=index_to_delete).reset_index(drop=True)
                    save_data(st.session_state.library_df, LIBRARY_FILE)
                    st.success(f"🗑️ Book '{book_to_delete_title}' has been deleted.")
                    st.rerun()
        else:
            st.info("There are no books in the library to delete.")

# 3. Library Page
elif page == "Library":
    st.header("📖 Your Digital Bookshelf")
    if not st.session_state.library_df.empty:
        num_columns = 3
        cols = st.columns(num_columns)
        
        for index, row in st.session_state.library_df.iterrows():
            with cols[index % num_columns]:
                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px solid #C0E6BA; border-radius: 8px; padding: 15px; margin-bottom: 10px; min-height: 180px;">
                        <h3 style="color: #013237;">{row['Title']}</h3>
                        <p style="color: #555;">by {row['Author']}</p>
                        <span style="background-color: #EAF9E7; color: #4CA771; padding: 3px 8px; border-radius: 5px; font-size: 14px;">
                            {row['Genre']} | {row['Pages']} pages
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    status_options = ["Read", "Reading", "Not Started"]
                    current_status_index = status_options.index(row['Status']) if row['Status'] in status_options else 2
                    
                    new_status = st.selectbox(
                        "Update Status", options=status_options, index=current_status_index,
                        key=f"status_{index}", label_visibility="collapsed"
                    )

                    if new_status != row['Status']:
                        st.session_state.library_df.loc[index, 'Status'] = new_status
                        save_data(st.session_state.library_df, LIBRARY_FILE)
                        st.rerun()
    else: 
        st.info("Your library is empty. An admin must add books to start your collection!")

# 4. Search Page
elif page == "Search":
    st.header("🔍 Find a Book")
    search_query = st.text_input("", placeholder="Search by Title, Author, or Genre...", label_visibility="collapsed")
    if search_query:
        query = search_query.lower()
        results_df = st.session_state.library_df[
            st.session_state.library_df['Title'].str.lower().str.contains(query) |
            st.session_state.library_df['Author'].str.lower().str.contains(query) |
            st.session_state.library_df['Genre'].str.lower().str.contains(query)
        ]
        st.markdown(f"Found **{len(results_df)}** matching books.")
        if not results_df.empty:
            st.dataframe(results_df, use_container_width=True, hide_index=True)
    else:
        st.info("Enter a search term to find books in your library.")
