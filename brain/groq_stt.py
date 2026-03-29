import os
import io
import traceback

try:
    import groq
except ImportError:
    groq = None

def transcribe_audio_groq(audio_bytes: bytes) -> str:
    if not groq:
        return "ERROR: Groq library not installed"
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "ERROR: GROQ_API_KEY missing from environment"
    
    if len(audio_bytes) < 100:
        return "" # Ignore tiny chunks (silence/header only)

    try:
        client = groq.Groq(api_key=api_key)
        # Using a tuple (filename, file_object)
        # Wrapping bytes in BytesIO is safer for some client implementations
        audio_file = io.BytesIO(audio_bytes)
        
        transcription = client.audio.transcriptions.create(
            file=("audio.webm", audio_file),
            model="whisper-large-v3-turbo",
            response_format="json",
            # Optional: language="en" 
        )
        return transcription.text.strip()
    except Exception as e:
        err_msg = str(e)
        print(f"[Groq STT Error] {err_msg}")
        # Return error string so it can be emitted to user via Socket
        if "401" in err_msg: return "ERROR: Invalid API Key"
        if "429" in err_msg: return "ERROR: Rate Limit Exceeded"
        return f"ERROR: {err_msg[:50]}"
