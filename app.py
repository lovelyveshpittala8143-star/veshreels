import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

st.set_page_config(page_title="VeshReels", page_icon="🎬", layout="wide")

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# --- Handle Google OAuth Callback ---
if "code" in st.query_params:
    try:
        supabase.auth.exchange_code_for_session({"auth_code": st.query_params["code"]})
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

session = supabase.auth.get_session()

if session:
    # --- LOGGED IN VIEW ---
    st.title("🎬 VeshReels")
    st.success(f"Logged in as: {session.user.email}")
    
    col1, col2 = st.columns([6,1])
    with col2:
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.rerun()

    st.write("---")
    
    # --- VIDEO UPLOAD ---
    st.subheader("Upload Your Reel")
    st.caption("Record your reel on your phone first, then upload it here")
    
    uploaded_file = st.file_uploader(
        "Choose a video file", 
        type=["mp4", "mov", "avi", "mkv"],
        help="Upload the reel you recorded on Instagram/TikTok"
    )

    if uploaded_file is not None:
        # Show the video
        st.video(uploaded_file)
        
        st.write("**Video details:**")
        st.write(f"Filename: {uploaded_file.name}")
        st.write(f"Size: {round(uploaded_file.size / 1024, 2)} MB")
        
        # Save to Supabase Storage
        if st.button("Save Reel to Cloud", type="primary"):
            with st.spinner("Uploading to Supabase..."):
                try:
                    # Create unique filename
                    file_ext = uploaded_file.name.split(".")[-1]
                    file_name = f"{session.user.id}/{uuid.uuid4()}.{file_ext}"
                    
                    # Upload to Supabase Storage bucket called 'reels'
                    res = supabase.storage.from_("reels").upload(
                        file=file_name,
                        file_options={"content-type": uploaded_file.type},
                        path=file_name,
                        file=uploaded_file.getvalue()
                    )
                    
                    st.success("Reel uploaded successfully!")
                    st.balloons()
                    
                    # Get public URL
                    url = supabase.storage.from_("reels").get_public_url(file_name)
                    st.write("**Share link:**")
                    st.code(url)
                    
                except Exception as e:
                    st.error(f"Upload failed: {e}")
                    st.caption("Make sure you created a 'reels' bucket in Supabase Storage and set it to public")

    # Show user's uploaded reels
    st.write("---")
    st.subheader("Your Uploaded Reels")
    try:
        files = supabase.storage.from_("reels").list(session.user.id)
        if files:
            for file in files:
                url = supabase.storage.from_("reels").get_public_url(f"{session.user.id}/{file['name']}")
                st.video(url)
                st.caption(file['name'])
        else:
            st.info("No reels uploaded yet. Upload your first one above!")
    except:
        st.caption("Create a 'reels' bucket in Supabase Storage to save videos")

else:
    # --- LOGGED OUT VIEW ---
    st.title("🎬 VeshReels")
    st.write("Login to upload and save your reels")

    res = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {"redirect_to": st.secrets.get("REDIRECT_URL", "")}
    })
    st.link_button("Login with Google", res.url, type="primary", use_container_width=True)
