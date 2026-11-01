import os
import subprocess
from pathlib import Path
import yt_dlp

def download_youtube_video(youtube_url: str, output_dir: str) -> str:
    """Downloads the YouTube lecture as a standard MP4 (up to 720p for fast processing)."""
    output_template = os.path.join(output_dir, "source_lecture.%(ext)s")
    
    ydl_opts = {
        # Prefer 720p H.264 MP4 so FFmpeg and players handle it cleanly without huge file sizes
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(youtube_url, download=True)
        
    final_path = os.path.join(output_dir, "source_lecture.mp4")
    if not os.path.exists(final_path):
        # Fallback if yt-dlp saved with a different extension
        for file in os.listdir(output_dir):
            if file.startswith("source_lecture"):
                return os.path.join(output_dir, file)
    return final_path

def render_subtitled_video(video_path: str, srt_path: str, output_path: str, burn_in: bool = True) -> tuple[bool, str]:
    """Burns subtitles into video frames or embeds them as a soft track using FFmpeg."""
    if burn_in:
        # Escape path for cross-platform FFmpeg subtitles filter
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