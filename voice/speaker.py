import pyttsx3

# Initialize engine only once
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()


# Temporary testing block
if __name__ == "__main__":
    speak("Testing speaker module")