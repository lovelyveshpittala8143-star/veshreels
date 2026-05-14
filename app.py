import streamlit as st
import requests
import uuid
import jwt

st.set_page_config(page_title="VeshReels", page_icon="🎬", layout="wide")

# HARDCODED - no secrets line break issues
SUPABASE_URL = "https://sjmnakvibeplycipgkgj.supabase.co"
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
REDIRECT_URL = "https://veshreels-mayj2zwnuucbmcgarvtbgz.streamlit.app"

st.markdown("""
    <style>
.block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION MANAGEMENT ---
if "user" not in st.session_state:
    st.session_state.user = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None

# --- HANDLE GOOGLE REDIRECT ---
if "access_token" in st.query_params and not st.session_state.user:
    try:
        access_token = st.query_params["access_token"]
        # Get user info from token
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {access_token}"}
        user_res = requests.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)
        if user_res.status_code == 200:
            st.session_state.user = user_res.json()
            st.session_state.access_token = access_token
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

# --- HELPER: Supabase requests with auth ---
def supa_request(method, path, json_data=None, files=None):
    url = f"{SUPABASE_URL}{path}"
    headers = {"apikey": SUPABASE_KEY}
    if st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"

    if files:
        return requests.request(method, url, headers=headers, files=files)
    return requests.request(method, url, headers=headers, json=json_data)

if st.session_state.user:
    # --- LOGGED IN VIEW ---
    user = st.session_state.user
    col1, col2, col3 = st.columns([1,3,1])
    with col1:
        st.title("🎬")
    with col2:
        st.title("VeshReels")
    with col3:
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.access_token = None
            st.rerun()

    st.caption(f"@{user['email'].split('@')[0]}")
    st.write("---")

    # --- UPLOAD SECTION ---
    with st.expander("⬆️ Upload New Reel", expanded=False):
        uploaded_file = st.file_uploader(
            "Upload MP4/MOV",
            type=["mp4", "mov", "avi"],
            label_visibility="collapsed"
        )
        caption = st.text_input("Add a caption", placeholder="Describe your reel...")

        if uploaded_file and st.button("Post Reel", type="primary", use_container_width=True):
            with st.spinner("Posting..."):
                try:
                    file_ext = uploaded_file.name.split(".")[-1]
                    file_name = f"{user['id']}/{uuid.uuid4()}.{file_ext}"

                    # Upload to storage
                    files = {'file': (file_name, uploaded_file.getvalue(), uploaded_file.type)}
                    up_res = supa_request("POST", f"/storage/v1/object/reels/{file_name}", files=files)
                    up_res.raise_for_status()

                    # Insert post record
                    post_data = {
                        "user_id": user['id'],
                        "user_email": user['email'],
                        "video_path": file_name,
                        "caption": caption
                    }
                    ins_res = supa_request("POST", "/rest/v1/posts", json_data=post_data)
                    ins_res.raise_for_status()

                    st.success("Posted!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Upload failed: {e}")

    # --- SCROLLING FEED ---
    st.subheader("For You")
    try:
        posts_res = supa_request("GET", "/rest/v1/posts?select=*&order=created_at.desc")
        posts = posts_res.json()
        if posts:
            for post in posts:
                video_url = f"{SUPABASE_URL}/storage/v1/object/public/reels/{post['video_path']}"
                with st.container():
                    st.video(video_url)
                    st.markdown(f"**@{post['user_email'].split('@')[0]}**")
                    if post['caption']:
                        st.write(post['caption'])
                    st.write("---")
        else:
            st.info("No reels yet. Be the first to post!")
    except Exception as e:
        st.error("Feed error. Did you create the 'posts' table and 'reels' bucket?")

else:
    # --- LOGGED OUT VIEW ---
    st.title("🎬 VeshReels")
    st.subheader("Watch and share short videos")

    # Build Google OAuth URL manually to use Implicit Flow instead of PKCE
    google_url = f"{SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to={REDIRECT_URL}"
    st.link_button("Login with Google", google_url, type="primary", use_container_width=True)
