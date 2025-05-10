import speech_recognition as sr

def listen():
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print("Adjusting for ambient noise... Please wait.")
            recognizer.adjust_for_ambient_noise(source, duration=1)  # Adjust based on surrounding noise
            print("Listening for your command...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Got the audio input!")
            return audio

    except sr.WaitTimeoutError:
        print("Listening timed out while waiting for phrase to start.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from the speech recognition service; {e}")
        return None
    except sr.UnknownValueError:
        print("Speech Recognition could not understand the audio.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while listening: {e}")
        return None
