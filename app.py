# app.py
import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
from datetime import date
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
# Sets the basic configuration for the Streamlit page.
st.set_page_config(
    page_title="Finoptiv Library",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
# This function loads a local CSS file to apply custom styles to the app.
def local_css(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # If the CSS file isn't found, display an error instead of crashing.
        st.error(f"CSS file not found: {file_name}. Make sure 'style.css' is in the same directory.")

# Apply the custom styles from 'style.css'.
# You would need to create a style.css file for this to work.
# local_css("style.css")

# --- DATA MANAGEMENT & SECURITY ---
LIBRARY_FILE = 'library.csv'
LOG_FILE = 'daily_log.csv'
ADMIN_PASSWORD = "admin123" # A more secure password should be used in a real application.

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
    """Saves a DataFrame to a CSV file."""
    df.to_csv(file_path, index=False)

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
    st.markdown("<h1 style='text-align: center; color: #4CA771;'>Finoptiv Library</h1>", unsafe_allow_html=True)
    
    # Dynamically set menu options based on admin login status.
    options = ["Dashboard", "Library", "Search"]
    icons = ["bar-chart-line-fill", "book-half", "search"]
    if st.session_state.admin_access:
        options.insert(1, "Admin Panel")
        icons.insert(1, "shield-lock-fill")

    # The main navigation menu.
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
    
    st.markdown("<hr class='sidebar-hr'>", unsafe_allow_html=True)

    # Admin login/logout section.
    if not st.session_state.admin_access:
        with st.expander("Admin Login", expanded=False):
            password = st.text_input("Password", type="password", key="admin_password")
            if st.button("Login", key="login_button"):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_access = True
                    st.success("Login successful!")
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
        <div style='text-align: center; padding: 10px; color: #013237;'>
            Developed by <b>Sourab</b><br>
            <a href="https://finoptiv.vercel.app" target="_blank" style='color: #4CA771;'>finoptiv.vercel.app</a>
        </div>
        """, unsafe_allow_html=True)

# --- PAGE RENDERING LOGIC ---

# 1. Dashboard Page
if page == "Dashboard":
    st.title("📚 Finoptiv Books")
    st.markdown("Time to relax and read a book.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your Reading Progress")
        total_books = len(st.session_state.library_df)
        if total_books > 0:
            read_books = len(st.session_state.library_df[st.session_state.library_df['Status'] == 'Read'])
            progress = (read_books / total_books) * 100
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = progress,
                title = {'text': f"<b>{read_books} of {total_books} Books Completed</b>", 'font': {'size': 20, 'color': '#013237'}},
                gauge = {
                    'axis': {'range': [None, 100]}, 'bar': {'color': "#4CA771"},
                    'steps': [{'range': [0, 100], 'color': '#EAF9E7'}],
                }
            ))
            fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
        else:
            st.info("Add books to your library to see your progress.")
    
    with col2:
        st.subheader("Top 5 Genres")
        if not st.session_state.library_df.empty:
            genre_counts = st.session_state.library_df['Genre'].value_counts().nlargest(5)
            fig = go.Figure(go.Bar(
                x=genre_counts.index, y=genre_counts.values,
                marker_color=['#4CA771', '#6FC276', '#93D88B', '#B7EEA4', '#DCFFC3']
            ))
            fig.update_layout(
                title_text="Genre Distribution", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color='#013237'
            )
            st.plotly_chart(fig, use_container_width=True)
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
            
            if col_submit.form_submit_button("Submit All Logs"):
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
    st.header("🛠️ Admin Panel: Manage Library")
    
    # Using tabs for a cleaner admin interface.
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
                    # Check for duplicates before adding.
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
            # Dropdown to select a book to edit.
            book_to_edit_title = st.selectbox("Select a book to edit", options=st.session_state.library_df['Title'])
            
            if book_to_edit_title:
                book_index = st.session_state.library_df[st.session_state.library_df['Title'] == book_to_edit_title].index[0]
                book_data = st.session_state.library_df.loc[book_index]

                with st.form("edit_book_form"):
                    st.write(f"Editing details for: **{book_to_edit_title}**")
                    
                    # Form fields are pre-populated with the existing book data.
                    new_title = st.text_input("Book Title", value=book_data['Title'])
                    new_author = st.text_input("Author Name", value=book_data['Author'])
                    new_genre = st.text_input("Genre", value=book_data['Genre'])
                    new_pages = st.number_input("Total Pages", min_value=1, step=1, value=int(book_data['Pages']))
                    status_options = ["Not Started", "Reading", "Read"]
                    current_status_index = status_options.index(book_data['Status'])
                    new_status = st.selectbox("Reading Status", options=status_options, index=current_status_index)

                    if st.form_submit_button("Update Book"):
                        # Update the DataFrame with the new values.
                        st.session_state.library_df.loc[book_index] = [new_title, new_author, new_genre, new_pages, new_status]
                        save_data(st.session_state.library_df, LIBRARY_FILE)
                        st.success(f"✅ Book '{new_title}' updated successfully!")
                        st.rerun()
        else:
            st.info("There are no books in the library to edit.")

    with tab3:
        st.subheader("Delete a Book")
        if not st.session_state.library_df.empty:
            # Dropdown to select a book to delete.
            book_to_delete_title = st.selectbox("Select a book to delete", options=st.session_state.library_df['Title'], key="delete_select")

            if book_to_delete_title:
                st.warning(f"**Warning:** You are about to delete **'{book_to_delete_title}'**. This action cannot be undone.")
                
                # Confirmation checkbox to prevent accidental deletion.
                confirm_delete = st.checkbox("I understand and want to delete this book.")

                if st.button("Delete Book Permanently", disabled=not confirm_delete):
                    book_index_to_delete = st.session_state.library_df[st.session_state.library_df['Title'] == book_to_delete_title].index[0]
                    st.session_state.library_df = st.session_state.library_df.drop(index=book_index_to_delete).reset_index(drop=True)
                    save_data(st.session_state.library_df, LIBRARY_FILE)
                    st.success(f"🗑️ Book '{book_to_delete_title}' has been deleted.")
                    st.rerun()
        else:
            st.info("There are no books in the library to delete.")

# 3. Library Page
elif page == "Library":
    st.header("📖 Your Digital Bookshelf")
    if not st.session_state.library_df.empty:
        # Display books in a grid layout.
        num_columns = 3
        cols = st.columns(num_columns)
        
        for index, row in st.session_state.library_df.iterrows():
            with cols[index % num_columns]:
                with st.container():
                    # Custom HTML for the book card.
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
                    
                    # Dropdown to update the reading status of a book.
                    new_status = st.selectbox(
                        "Update Status",
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
    st.header("🔍 Find a Book")
    search_query = st.text_input("", placeholder="Search by Title, Author, or Genre...", label_visibility="collapsed")
    if search_query:
        query = search_query.lower()
        # Search across multiple columns.
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
