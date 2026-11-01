import streamlit as st
from faster_whisper import WhisperModel

def format_srt_timestamp(seconds: float) -> str:
    """Converts floating-point seconds into strict SRT format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    if milliseconds == 1000:
        secs += 1
        milliseconds = 0
        if secs == 60:
            minutes += 1
            secs = 0
            if minutes == 60:
                hours += 1
                minutes = 0
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

@st.cache_resource
def load_whisper_model(model_size: str, use_gpu: bool) -> WhisperModel:
    """Caches the Whisper model in memory so Streamlit doesn't reload it on every click."""
    device = "cuda" if use_gpu else "cpu"
    compute_type = "float16" if use_gpu else "int8"
    return WhisperModel(model_size, device=device, compute_type=compute_type)

def transcribe_to_arabic_segments(video_path: str, model: WhisperModel) -> list[dict]:
    """Transcribes the lecture audio into timestamped Arabic segments."""
    segments, _ = model.transcribe(
        video_path,
        language="ar",
        task="transcribe",                  # Transcribe in original Classical Arabic first
        beam_size=5,
        vad_filter=True,                    # Strips silence to stop Whisper hallucinations
        vad_parameters=dict(min_silence_duration_ms=500),
        condition_on_previous_text=False
    )
    
    arabic_segments = []
    for idx, seg in enumerate(segments, start=1):
        arabic_segments.append({
            "index": idx,
            "start": format_srt_timestamp(seg.start),
            "end": format_srt_timestamp(seg.end),
            "text": seg.text.strip()
        })
    return arabic_segments

def save_segments_to_srt(segments: list[dict], srt_path: str):
    """Writes a list of segment dicts to a valid .srt file."""
    with open(srt_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"{seg['index']}\n")
            f.write(f"{seg['start']} --> {seg['end']}\n")
            f.write(f"{seg['text']}\n\n")