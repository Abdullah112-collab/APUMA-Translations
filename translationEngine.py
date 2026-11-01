from faster_whisper import WhisperModel

# Load the model. 'cuda' runs on NVIDIA GPUs. Use 'float16' for efficiency.
# For CPU execution, use device="cpu" and compute_type="int8"
model = WhisperModel("large-v3", device="cuda", compute_type="float16")

# Set task="translate" to translate foreign audio into English text
segments, info = model.transcribe("lecture_video.mp4", task="translate", beam_size=5)

print(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")

# Print the text with timestamps
for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
