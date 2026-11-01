import os
import tempfile
import traceback
import streamlit as st

st.set_page_config(page_title="APUMA Dars Translator", layout="centered")

st.title("Islamic Lecture (Dars) Auto-Translator & Subtitler")
st.write("Upload a lecture video -> Whisper transcribes Arabic -> Gemini translates to English -> FFmpeg burns subtitles.")

def get_default_api_key() -> str:
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("Configuration")
    gemini_api_key = st.text_input(
        "Gemini API Key",
        value=get_default_api_key(),
        type="password",
        help="Get a free key at aistudio.google.com"
    )
    
    whisper_model_size = st.selectbox(
        "Whisper Model Size",
        ["small", "medium", "large-v3"],
        index=0,
        help="Use 'small' on Streamlit Community Cloud (1GB RAM limit). Use 'large-v3' locally or on GPU."
    )
    use_gpu = st.checkbox("Use NVIDIA GPU (CUDA)", value=False)
    burn_in = st.radio(
        "Subtitle Rendering Mode",
        ["Burn-In (Hardcoded onto video frames)", "Soft-Sub (Instant embedded track - 3 seconds)"]
    ) == "Burn-In (Hardcoded onto video frames)"

uploaded_video = st.file_uploader(
    "Upload Lecture Video (.mp4, .mkv, .mov)", 
    type=["mp4", "mkv", "mov"]
)

if st.button("Translate & Generate Subtitled Video", type="primary", disabled=not (uploaded_video and gemini_api_key)):
    from media_handler import save_uploaded_video, render_subtitled_video
    from transcriber import load_whisper_model, transcribe_to_arabic_segments, save_segments_to_srt
    from translator import translate_segments_with_gemini

    with tempfile.TemporaryDirectory() as tmpdir:
        status = st.status("Running End-to-End Translation Pipeline...", expanded=True)

        try:
            # STEP 1: Save Uploaded Video
            status.write("1/4 Saving uploaded video file...")
            video_path = save_uploaded_video(uploaded_video, tmpdir)
            status.write(f"✅ Video loaded (`{uploaded_video.name}`).")

            # STEP 2: Transcribe Arabic Audio with Whisper
            status.write(f"2/4 Transcribing Arabic speech using Whisper (`{whisper_model_size}`)...")
            model = load_whisper_model(whisper_model_size, use_gpu)
            arabic_segments = transcribe_to_arabic_segments(video_path, model)
            
            arabic_srt_path = os.path.join(tmpdir, "arabic_transcript.srt")
            save_segments_to_srt(arabic_segments, arabic_srt_path)
            status.write(f"✅ Transcribed {len(arabic_segments)} Arabic subtitle segments.")

            # STEP 3: Translate with Gemini API
            status.write("3/4 Translating into English with Gemini 2.5 Flash...")
            progress_bar = status.progress(0.0)
            english_segments = translate_segments_with_gemini(
                arabic_segments,
                api_key=gemini_api_key,
                batch_size=25,
                progress_callback=lambda p: progress_bar.progress(p)
            )
            
            english_srt_path = os.path.join(tmpdir, "english_translated.srt")
            save_segments_to_srt(english_segments, english_srt_path)
            status.write("✅ English translation complete.")

            # STEP 4: Burn or Embed Subtitles with FFmpeg
            output_video_path = os.path.join(tmpdir, "subtitled_dars.mp4")
            status.write("4/4 Rendering final video with FFmpeg...")
            success, error_log = render_subtitled_video(
                video_path=video_path,
                srt_path=english_srt_path,
                output_path=output_video_path,
                burn_in=burn_in
            )

            if success:
                status.update(label="Pipeline Complete!", state="complete", expanded=False)
                st.success("Your translated lecture is ready!")

                with open(output_video_path, "rb") as vf:
                    st.session_state["final_video"] = vf.read()
                with open(english_srt_path, "rb") as ef:
                    st.session_state["en_srt"] = ef.read()
                with open(arabic_srt_path, "rb") as af:
                    st.session_state["ar_srt"] = af.read()
                st.session_state["original_filename"] = uploaded_video.name
            else:
                status.update(label="FFmpeg Error", state="error")
                st.error("FFmpeg failed to render the video:")
                st.code(error_log)

        except Exception as e:
            status.update(label="Pipeline Failed", state="error")
            st.error(f"Error: {str(e)}")
            st.code(traceback.format_exc())

if "final_video" in st.session_state:
    st.divider()
    st.subheader("Download Outputs")
    base_name = os.path.splitext(st.session_state.get("original_filename", "dars"))[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "Download Subtitled Video (.mp4)",
            data=st.session_state["final_video"],
            file_name=f"{base_name}_english_subtitled.mp4",
            mime="video/mp4",
            type="primary"
        )
    with col2:
        st.download_button(
            "Download English (.srt)",
            data=st.session_state["en_srt"],
            file_name=f"{base_name}_english.srt",
            mime="text/plain"
        )
    with col3:
        st.download_button(
            "Download Arabic (.srt)",
            data=st.session_state["ar_srt"],
            file_name=f"{base_name}_arabic.srt",
            mime="text/plain"
        )