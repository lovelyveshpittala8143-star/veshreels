import streamlit as st
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
from groq import Groq
import tempfile
import os
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="VeshReels", page_icon="🎬", layout="wide")

@st.cache_resource
def init_connections():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
    return supabase, groq

supabase, groq = init_connections()

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("VeshReels 🎬")
    st.subheader("Create & Share Videos - 100% Free")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.rerun()
            except Exception as e:
                st.error("Login failed. Sign Up first.")
    with col2:
        if st.button("Sign Up", use_container_width=True):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.success("Account created! Now click Login.")
            except Exception as e:
                st.error("Signup failed. Email already used.")
    st.stop()

user = st.session_state.user

st.sidebar.title(f"Hey, {user.email.split('@')[0]} 👋")
page = st.sidebar.radio("Menu", ["🏠 Feed", "🎬 Create Reel", "👤 My Reels"])
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

if page == "🎬 Create Reel":
    st.title("Create New Reel 🎬")
    uploaded_video = st.file_uploader("1. Upload video", type=["mp4", "mov"])
    text_overlay = st.text_input("2. Text on video", "VeshReels 🔥")
    music_file = st.file_uploader("3. Background music - optional", type=["mp3"])
    generate_captions = st.toggle("4. Auto-captions", value=True)

    if uploaded_video and st.button("Post Reel", type="primary"):
        with st.spinner("Making your reel... 30-60 seconds"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as t_video:
                t_video.write(uploaded_video.read())
                video_path = t_video.name

            clip = VideoFileClip(video_path)
            txt_clip = TextClip(text_overlay, fontsize=60, color='white', font='Arial-Bold', stroke_color='black', stroke_width=2)
            txt_clip = txt_clip.set_pos(('center','bottom')).set_duration(clip.duration)
            final_clip = CompositeVideoClip([clip, txt_clip])

            if music_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as t_audio:
                    t_audio.write(music_file.read())
                    audio_path = t_audio.name
                audio = AudioFileClip(audio_path).subclip(0, clip.duration)
                final_clip = final_clip.set_audio(audio)

            caption_text = ""
            if generate_captions:
                try:
                    with open(video_path, "rb") as f:
                        transcription = groq.audio.transcriptions.create(
                            file=(video_path, f.read()),
                            model="whisper-large-v3",
                            response_format="text"
                        )
                    caption_text = transcription.strip()
                except:
                    caption_text = ""

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as final_video:
                final_clip.write_videofile(final_video.name, codec="libx264", audio_codec="aac", fps=24, logger=None)
                final_path = final_video.name

            video_name = f"{user.id}_{int(datetime.now().timestamp())}.mp4"
            with open(final_path, "rb") as f:
                supabase.storage.from_("reels").upload(video_name, f)
            video_url = supabase.storage.from_("reels").get_public_url(video_name)

            supabase.table("videos").insert({
                "user_id": user.id,
                "user_email": user.email,
                "video_url": video_url,
                "caption": caption_text,
                "text_overlay": text_overlay
            }).execute()

            st.success("Posted! Check the Feed 🎉")
            st.balloons()

elif page == "🏠 Feed":
    st.title("VeshReels Feed 🎬")
    videos = supabase.table("videos").select("*").order("created_at", desc=True).limit(20).execute()
    if not videos.data:
        st.info("No reels yet. Be the first to post!")
    else:
        for vid in videos.data:
            st.write(f"**@{vid['user_email'].split('@')[0]}**")
            st.video(vid['video_url'])
            if vid['caption']:
                st.caption(f"💬 {vid['caption']}")
            st.write("---")

elif page == "👤 My Reels":
    st.title("My Reels")
    videos = supabase.table("videos").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
    if not videos.data:
        st.info("You haven't posted any reels yet")
    else:
        for vid in videos.data:
            st.video(vid['video_url'])
            st.caption(f"Text: {vid['text_overlay']}")
            if st.button("Delete", key=vid['id']):
                supabase.table("videos").delete().eq("id", vid['id']).execute()
                st.rerun()
            st.write("---")
