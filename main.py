from core.listener import listen
from voice.speaker import speak
from brain.ai_engine import ask_ai
from core.commands import handle_command
from langdetect import detect as detect_lang

print("Jarvis Activated. Say something...")
speak("Jarvis Activated. How can I help you?")

while True:
    user_input = listen()

    if not user_input:
        continue

    user_input = user_input.strip().lower()

    if user_input in ["exit", "stop", "goodbye", "band karo", "बंद करो"]:
        speak("Goodbye Ishita.")
        break

    print("You:", user_input)

    # Check for system commands first (open/close apps)
    result = handle_command(user_input)
    if result:
        print("Jarvis:", result)
        speak(result)
        continue

    # Detect language and send to AI
    try:
        lang = detect_lang(user_input)
        lang = 'hi' if lang == 'hi' else 'en'
    except Exception:
        lang = 'en'

    print(f"[Lang detected: {lang}]")

    response = ask_ai(user_input, lang=lang)

    print("Jarvis:", response)

    speak(response)
