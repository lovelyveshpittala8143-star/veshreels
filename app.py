import streamlit as st
from supabase import create_client
import uuid

st.set_page_config(page_title="VeshReels", page_icon="🎬", layout="wide")

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

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# Get session - Supabase handles OAuth redirect automatically
session = supabase.auth.get_session()

if session:
    # --- LOGGED IN VIEW ---
    col1, col2, col3 = st.columns([1,3,1])
    with col1:
        st.title("🎬")
    with col2:
        st.title("VeshReels")
    with col3:
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.rerun()

    st.caption(f"@{session.user.email.split('@')[0]}")
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
                    file_name = f"{session.user.id}/{uuid.uuid4()}.{file_ext}"

                    supabase.storage.from_("reels").upload(
                        path=file_name,
                        file=uploaded_file.getvalue(),
                        file_options={"content-type": uploaded_file.type}
                    )

                    supabase.table("posts").insert({
                        "user_id": session.user.id,
                        "user_email": session.user.email,
                        "video_path": file_name,
                        "caption": caption
                    }).execute()

                    st.success("Posted!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Upload failed: {e}")

    # --- SCROLLING FEED ---
    st.subheader("For You")
    try:
        posts = supabase.table("posts").select("*").order("created_at", desc=True).execute()
        if posts.data:
            for post in posts.data:
                video_url = supabase.storage.from_("reels").get_public_url(post['video_path'])
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

    res = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {"redirect_to": st.secrets["REDIRECT_URL"]}
    })
    st.link_button("Login with Google", res.url, type="primary", use_container_width=True)
