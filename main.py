from core.listener import listen
from voice.speaker import speak
import time

STATE = "ACTIVE"

while True:

    if STATE == "PASSIVE":
        text = listen()

        if text and "hey jarvis" in text:
            speak("Yes Ishita?")
            STATE = "ACTIVE"

    elif STATE == "ACTIVE":
        text = listen()

        if text:
            text = text.strip().lower()
            print("DEBUG TEXT:", repr(text))

            if any(word in text for word in ["stop", "exit", "sleep", "go back"]):
                print("STOP DETECTED")
                speak("Okay, going to sleep.")
                break
            else:
                speak("You said " + text)