import os
import subprocess
from pathlib import Path
import yt_dlp

def download_youtube_video(youtube_url: str, output_dir: str) -> str:
    """Downloads the YouTube lecture with bot-bypass fallbacks and format flexibility."""
    output_template = os.path.join(output_dir, "source_lecture.%(ext)s")
    
    ydl_opts = {
        # 1. Flexible format: Grab up to 720p in whatever codec exists, then force MP4 merge
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_template,
        
        # 2. Bypass YouTube bot-checks using alternative player clients
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'web_creator', 'web']
            }
        },
        
        # 3. Network resiliency
        'socket_timeout': 30,
        'retries': 5,
        'noplaylist': True,
        
        # 4. Don't hide errors so we can catch and display them
        'quiet': False,
        'no_warnings': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as e:
        raise RuntimeError(f"YouTube Download Error: {str(e)}")

    # Locate the downloaded file (accounting for potential extension differences)
    final_path = os.path.join(output_dir, "source_lecture.mp4")
    if os.path.exists(final_path):
        return final_path
        
    for file in os.listdir(output_dir):
        if file.startswith("source_lecture"):
            return os.path.join(output_dir, file)
            
    raise FileNotFoundError("The video downloaded, but the output file could not be found.")

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