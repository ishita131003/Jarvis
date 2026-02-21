import speech_recognition as sr

recognizer = sr.Recognizer()

def listen():
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print("You said:", text)
        return text.lower()
    except sr.UnknownValueError:
        print("Could not understand audio")
        return None
    except sr.RequestError:
        print("Speech service error")
        return None


# Temporary testing block
if __name__ == "__main__":
    while True:
        listen()