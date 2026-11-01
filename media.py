import os
import subprocess
from pathlib import Path

def save_uploaded_video(uploaded_file, output_dir: str) -> str:
    """Saves the Streamlit UploadedFile object to a temporary local path in chunks."""
    ext = Path(uploaded_file.name).suffix or ".mp4"
    video_path = os.path.join(output_dir, f"source_lecture{ext}")
    
    uploaded_file.seek(0)
    with open(video_path, "wb") as f:
        while chunk := uploaded_file.read(1024 * 1024):  # Read in 1MB chunks to save RAM
            f.write(chunk)
            
    return video_path

def render_subtitled_video(video_path: str, srt_path: str, output_path: str, burn_in: bool = True) -> tuple[bool, str]:
    """Burns subtitles into video frames or embeds them as a soft track using FFmpeg."""
    if burn_in:
        escaped_srt = Path(srt_path).as_posix().replace(":", r"\:")
        style = (
            "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,"
            "BackColour=&H80000000,BorderStyle=4,Outline=0,Shadow=0,MarginV=25"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"subtitles='{escaped_srt}':force_style='{style}'",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "copy",
            output_path
        ]
    else:
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
    return (result.returncode == 0 and os.path.exists(output_path)), result.stderr