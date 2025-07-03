import speech_recognition as sr

def voice_listener(callback):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Voice system is ready.")

    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=1)
                command = recognizer.recognize_google(audio)
                print(f"You said: {command}")
                callback(command.lower())
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            print("Didn't catch that.")
        except Exception as e:
            print(f"Voice error: {e}")
