import os
import asyncio
import edge_tts
import pygame
import speech_recognition as sr

# Bilingual Natural Neural Voice (Roman Urdu / Hindi aur English dono fluent bolta hai)
VOICE = "hi-IN-MadhurNeural"  # Agar female voice chahiye ho toh "hi-IN-SwaraNeural" kar sakte hain

async def generate_speech(text: str, output_file: str = "temp_response.mp3"):
    """Converts input text to realistic natural speech."""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)

def speak(text: str):
    """Generates audio and plays it via system speakers."""
    audio_path = "temp_response.mp3"
    try:
        asyncio.run(generate_speech(text, audio_path))
        
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.music.unload()
        pygame.mixer.quit()
        
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception as e:
        print(f"[TTS Error]: {e}")

def listen_microphone() -> str:
    """Captures audio from microphone and converts it to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n[Listening...] Speak into your microphone:")
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        audio = recognizer.listen(source)
        
    try:
        print("[Processing Voice...]")
        text = recognizer.recognize_google(audio, language="ur-PK")
        print(f"[Recognized]: {text}")
        return text
    except sr.UnknownValueError:
        print("[Voice Error]: Could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"[Service Error]: {e}")
        return ""

if __name__ == "__main__":
    speak("Suno, ab meri Urdu pronunciation bilkul saaf aur natural aayegi.")