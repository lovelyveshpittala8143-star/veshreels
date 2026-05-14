import streamlit as st
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
from groq import Groq
import tempfile
import os
from supabase import create_client, Client

st.set_page_config(page_title="VeshReels", page_icon="🎬", layout="wide")

@st.cache_resource
def init_connections():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return supabase, groq

supabase, groq = init_connections()

# Handle OAuth redirect from Google
if "code" in st.query_params:
    try:
        supabase.auth.exchange_code_for_session(st.query_params)
    except:
        pass
    st.query_params.clear()

# Check user session safely
if "user" not in st.session_state:
    try:
        session = supabase.auth.get_session()
        st.session_state.user = session.user if session else None
    except:
        st.session_state.user = None

if st.session_state.user is None:
    st.title("VeshReels 🎬")
    st.subheader("Create & Share Videos - 100% Free")

    # Google Login Button - YOUR URL IS HARDCODED HERE
    if st.button("🔐 Continue with Google", type="primary", use_container_width=True):
        supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "https://veshreels-oscqcpah5siaby32fsmhqk.streamlit.app/"
            }
        })
        st.rerun()

    st.markdown("<center>or</center>", unsafe_allow_html=True)

    with st.form("email_login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        col1, col2 = st.columns(2)
        with col1:
            login = st.form_submit_button("Login", use_container_width=True)
        with col2:
            signup = st.form_submit_button("Sign Up", use_container_width=True)

        if login:
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.rerun()
            except Exception as e:
                st.error("Login failed. Check email/password or Sign Up first.")
        if signup:
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.success("Account created! Check your email to confirm, then Login.")
            except Exception as e:
                st.error("Signup failed. Email may already exist.")
    st.stop()

# --- USER IS LOGGED IN ---
user = st.session_state.user
st.sidebar.title(f"Hey, {user.email.split('@')[0]} 👋")
if user.user_metadata.get("avatar_url"):
    st.sidebar.image(user.user_metadata.get("avatar_url"), width=50)

page = st.sidebar.radio("Menu", ["🏠 Feed", "🎬 Create Reel", "👤 My Reels"])
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# PASTE THE REST OF YOUR APP CODE HERE
st.write("You are logged in! Add your reel creation code here 👑")
