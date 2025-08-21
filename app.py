import streamlit as st
import os
import sqlite3
from scrape_youtube import extract_video_id, get_transcript, extract_metadata, download_thumbnail
from summarize_text import summarize_text
from init_db import initialize_database
import bcrypt

# Set page configuration
st.set_page_config(page_title="YouTube AI Video Summarizer", layout="wide")

st.markdown("""
    <style>
    /* Sidebar title */
    [data-testid="stSidebar"]::before {
        content: "📋 History & User Menu";
        display: block;
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        padding: 15px;
        color: #F5F5F5;
    }
    /* Center the input and limit width */
    .block-container {
        max-width: 800px;
        margin: auto;
        padding-top: 2rem;
    }
    /* Shorten text input and dropdown width */
    .stTextInput > div > div > input,
    .stSelectbox > div > div {
        max-width: 500px;
    }
    </style>
""", unsafe_allow_html=True)


# Initialize database on first load
if "db_initialized" not in st.session_state:
    initialize_database()
    st.session_state["db_initialized"] = True

# Functions for user handling
def get_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True

def get_languages():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT name FROM languages")
    langs = [row[0] for row in c.fetchall()]
    conn.close()
    return langs

def save_summary(username, url, summary, title):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO summaries (username, url, summary, title) VALUES (?, ?, ?, ?)", (username, url, summary, title))
    conn.commit()
    conn.close()


# Initialize session state for authentication and user info
if "users" not in st.session_state:
    st.session_state["users"] = {"admin": "password123"}
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# Clean button spacing via CSS
st.markdown(
    """
    <style>
    div.stButton > button {
        margin: 10px 0px 10px 0px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Account creation function
def create_account():
    st.markdown("<h1 style='text-align: center;'>Create Account</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])  # Centered narrow column
    with col2:
        new_username = st.text_input("Choose a Username")
        new_password = st.text_input("Choose a Password", type="password")

        if st.button("Sign Up"):
            if get_user(new_username):
                st.error("Username already exists.")
            elif new_username and new_password:
                if add_user(new_username, new_password):
                    st.success("Account created! Please log in.")
                    st.session_state["page"] = "login"
                    st.rerun()
                else:
                    st.error("Failed to create account.")
            else:
                st.error("Enter valid credentials.")

        st.markdown("---")
        st.write("Already have an account?")
        if st.button("Sign In"):
            st.session_state["page"] = "login"
            st.rerun()


# Login page function
def login():
    st.markdown("<h1 style='text-align: center;'>Login Page</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])  # Centered narrow column
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = get_user(username)
            if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["page"] = "main"
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown("---")
        st.write("Don't have an account?")
        if st.button("Create Account"):
            st.session_state["page"] = "create_account"
            st.rerun()

def display_history(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT url, summary, timestamp FROM summaries WHERE username = ? ORDER BY timestamp DESC", (username,))
    rows = c.fetchall()
    conn.close()

    if rows:
        st.sidebar.markdown("<h5>📜 Your Summaries:</h5>", unsafe_allow_html=True)
        for url, summary, timestamp in rows[:5]:  # Limit to last 5
            title, _ = extract_metadata(url)  # Get the title for display
            with st.sidebar.expander(f"{title} ({timestamp.split()[0]})"):
                st.markdown(f"[🔗 Watch Video]({url})", unsafe_allow_html=True)
                st.text(summary[:200] + "...")  # Show summary preview
    else:
        st.sidebar.info("No history yet. Summarize a video!")

# Main app after login
def main_app():
    if not st.session_state["authenticated"]:
        login()
        return
    st.sidebar.markdown(
    """
    <div style='padding: 20px; border-radius: 15px; text-align: center;'>
        <h3 style='margin-bottom: 20px;'>👋 Welcome, {}</h3>
    """.format(st.session_state["username"]),
    unsafe_allow_html=True
    )
    st.markdown(
    """
    <style>
    [data-testid="stSidebar"]::before {
        content: "📋 History & User Menu";
        display: block;
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        padding: 15px;
        color: var(--text-color);
        position: relative;
        top: 65px;
    }
    </style>
    """,
    unsafe_allow_html=True
    )


    # Display History in Sidebar
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT url, title, summary, timestamp FROM summaries WHERE username = ? ORDER BY timestamp DESC", (st.session_state["username"],))
    rows = c.fetchall()
    conn.close()

    st.sidebar.markdown("<h5 style='margin-top: 10px;'>📜 Your Summaries:</h5>", unsafe_allow_html=True)

    if rows:
        for url, title, summary, timestamp in rows[:5]:
            with st.sidebar.expander(f"{title or 'Video'} ({timestamp.split()[0]})", expanded=False):
                st.markdown(f"[🔗 Watch Video]({url})", unsafe_allow_html=True)
                st.markdown("**Full Summary:**")
                st.markdown(summary)
    else:
        st.sidebar.info("No history yet. Summarize a video!")

    # Logout Button
    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.session_state["page"] = "login"
        st.rerun()


    # App Title with image and layout fix
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        st.image(
            "https://i.pinimg.com/originals/3a/36/20/3a36206f35352b4230d5fc9f17fcea92.png",
            width=50
        )
    with col2:
        st.markdown("<h1 style='font-size: 45px;'>YouTube AI Video Summarizer</h1>", unsafe_allow_html=True)

    st.subheader("Enter YouTube URL:")
    st.write("Paste a YouTube link to summarize its content")
    url = st.text_input("URL")

    language = st.selectbox("Select language:", get_languages())

    if st.button("Summarize"):
        if url:
            title, channel = extract_metadata(url)

            colA, colB = st.columns(2)
            with colA:
                st.subheader("Title:")
                st.write(title)
                st.subheader("Channel:")
                st.write(channel)

            with colB:
                video_id = extract_video_id(url)
                download_thumbnail(video_id)
                st.image(
                    os.path.join(os.getcwd(), "thumbnail.jpg"),
                    caption='Thumbnail',
                    use_column_width=True
                )

            transcript = get_transcript(video_id)
            summary = summarize_text(transcript, lang=language)
            st.subheader("Video Summary:")
            st.write(summary)
            save_summary(st.session_state["username"], url, summary, title)
            st.success("Summary saved to history!")
        else:
            st.warning("Please enter a YouTube URL.")

# Routing logic
if st.session_state["page"] == "login":
    login()
elif st.session_state["page"] == "create_account":
    create_account()
elif st.session_state["page"] == "main":
    main_app()