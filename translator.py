import json
from google import genai
from google.genai import types

SYSTEM_INSTRUCTION = """You are an expert translator of Classical Arabic Islamic scholarly lectures (Duroos) into clear, dignified, and theologically accurate English subtitles.

Rules:
1. Preserve exact Islamic theological precision (e.g., translate 'Taqwa' as 'piety/God-consciousness (Taqwa)', 'Tawheed' as 'Oneness of Allah (Tawheed)', 'Bid'ah' as 'religious innovation (Bid'ah)').
2. When Quranic verses (Ayat) are quoted, use standard, recognized English translations (such as Saheeh International).
3. Keep honorifics concise and clear for subtitles (e.g., '(peace and blessings of Allah be upon him)' or '(may Allah be pleased with him)').
4. You will receive a JSON array of Arabic subtitle segments, each with an 'index' and 'text'.
5. Return ONLY a valid JSON array of objects with the exact same 'index' integers and the translated English 'text'. Do not merge, skip, or add indices."""

def translate_segments_with_gemini(
    arabic_segments: list[dict],
    api_key: str,
    batch_size: int = 25,
    progress_callback=None
) -> list[dict]:
    """Translates Arabic segments in batches using Gemini 2.5 Flash while keeping exact timestamps."""
    client = genai.Client(api_key=api_key)
    translated_segments = []
    total_batches = (len(arabic_segments) + batch_size - 1) // batch_size

    for batch_num, i in enumerate(range(0, len(arabic_segments), batch_size), start=1):
        batch = arabic_segments[i : i + batch_size]
        
        # Prepare lightweight payload for Gemini (only index and Arabic text)
        payload = [{"index": s["index"], "text": s["text"]} for s in batch]

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=json.dumps(payload, ensure_ascii=False),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        try:
            translated_batch = json.loads(response.text)
            trans_map = {item["index"]: item["text"] for item in translated_batch}
        except Exception:
            # Fallback if JSON parsing ever hiccups
            trans_map = {}

        for seg in batch:
            translated_segments.append({
                "index": seg["index"],
                "start": seg["start"],
                "end": seg["end"],
                "text": trans_map.get(seg["index"], seg["text"])
            })

        if progress_callback:
            progress_callback(batch_num / total_batches)

    return translated_segments