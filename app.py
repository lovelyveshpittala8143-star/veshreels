import streamlit as st
from supabase import create_client
from groq import Groq

st.set_page_config(page_title="VeshReels", page_icon="🎬", layout="wide")

@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- Handle Google OAuth Callback ---
if "code" in st.query_params:
    try:
        supabase.auth.exchange_code_for_session({"auth_code": st.query_params["code"]})
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

# --- Check if user is logged in ---
session = supabase.auth.get_session()

if session:
    # --- LOGGED IN VIEW ---
    st.title("🎬 VeshReels AI")
    st.success(f"Logged in as: {session.user.email}")

    if st.button("Logout"):
        supabase.auth.sign_out()
        st.rerun()

    st.write("---")
    st.subheader("Generate a Reel Script")
    prompt = st.text_area("Enter your reel idea:", height=150)

    if st.button("Generate Script"):
        if prompt:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            with st.spinner("Generating..."):
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Write a viral reel script for: {prompt}"}],
                    model="llama3-8b-8192",
                )
                st.write(chat_completion.choices[0].message.content)
        else:
            st.warning("Please enter an idea first.")

else:
    # --- LOGGED OUT VIEW - FIXED BUTTON ---
    st.title("🎬 VeshReels AI")
    st.write("Login to generate AI reel scripts")

    # This generates the Google login URL
    res = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {"redirect_to": st.secrets.get("REDIRECT_URL", "")}
    })

    # This button actually takes you to Google
    st.link_button("Login with Google", res.url, type="primary", use_container_width=True)
