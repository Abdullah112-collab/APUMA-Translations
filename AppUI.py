import streamlit as st
import subprocess
import tempfile
import os
from pathlib import Path

st.set_page_config(page_title="Dars Auto-Subtitler", layout="centered")
st.title("Auto-Subtitle Merger for Lectures")
st.write("Upload your lecture video and English `.srt` file. No video editing required.")

video_file = st.file_uploader("1. Upload Lecture Video (.mp4, .mkv, .mov)", type=["mp4", "mkv", "mov"])
srt_file = st.file_uploader("2. Upload Subtitle File (.srt)", type=["srt"])

mode = st.radio(
    "Choose Subtitle Mode:",
    [
        "Burn-In (Hardcoded onto video frames - works on all social media & players)",
        "Instant Soft-Sub (Embedded track - finishes in 3 seconds, zero quality loss)"
    ]
)

if st.button("Generate Subtitled Lecture", type="primary", disabled=not (video_file and srt_file)):
    with st.spinner("Processing video... Please wait."):
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "input_video.mp4")
            srt_path = os.path.join(tmpdir, "subtitles.srt")
            output_path = os.path.join(tmpdir, "subtitled_lecture.mp4")

            with open(video_path, "wb") as f:
                f.write(video_file.read())
            with open(srt_path, "wb") as f:
                f.write(srt_file.read())

            if "Burn-In" in mode:
                # Escape path for FFmpeg subtitles filter on Windows/Linux
                escaped_srt = Path(srt_path).as_posix().replace(":", r"\:")
                
                # Burn subtitles with clean readable styling (Font size 20, dark background box)
                style = "FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,BackColour=&H80000000,BorderStyle=4,Outline=0,Shadow=0,MarginV=25"
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-vf", f"subtitles='{escaped_srt}':force_style='{style}'",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                    "-c:a", "copy",
                    output_path
                ]
            else:
                # Instant soft-sub muxing without re-encoding video or audio
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", srt_path,
                    "-c:v", "copy",
                    "-c:a", "copy",
                    "-c:s", "mov_text",
                    "-metadata:s:s:0", "language=eng",
                    output_path
                ]

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0 and os.path.exists(output_path):
                st.success("Subtitled lecture generated!")
                with open(output_path, "rb") as out_f:
                    st.download_button(
                        label="Download Subtitled Lecture (.mp4)",
                        data=out_f.read(),
                        file_name=f"subtitled_{video_file.name}",
                        mime="video/mp4"
                    )
            else:
                st.error("FFmpeg encountered an error:")
                st.code(result.stderr)