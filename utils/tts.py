import pyttsx3
import threading
import pythoncom  # Required for COM initialization in threads

def _speak_thread(text):
    """Runs the speech engine in a separate thread to avoid conflicts."""
    pythoncom.CoInitialize()  # Explicitly initialize COM
    engine = pyttsx3.init()
    engine.setProperty("rate", 200)
    engine.say(text)
    engine.runAndWait()

def speak(text):
    """Speak function that runs in a separate thread."""
    thread = threading.Thread(target=_speak_thread, args=(text,))
    thread.start()
