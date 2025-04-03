import speech_recognition as sr

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=10)
            text = recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            print("❌ Listening timeout! No speech detected.")
            return "timeout"
        except sr.UnknownValueError:
            print("❌ Speech not understood.")
            return "unknown"
        except sr.RequestError:
            print("❌ Speech recognition service unavailable.")
            return "error"
