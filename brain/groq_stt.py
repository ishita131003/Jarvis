import os
import io
import traceback

try:
    import groq
except ImportError:
    groq = None

def transcribe_audio_groq(audio_bytes: bytes) -> str:
    if not groq:
        return ""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return ""
    try:
        client = groq.Groq(api_key=api_key)
        transcription = client.audio.transcriptions.create(
            file=("audio.webm", audio_bytes),
            model="whisper-large-v3-turbo",
            response_format="json",
        )
        return transcription.text.strip()
    except Exception as e:
        print(f"[Groq STT Error] {e}")
        traceback.print_exc()
        return ""
