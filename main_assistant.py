import re
from agent_core import chat
from voice_service import speak, listen_microphone

def clean_text_for_speech(raw_text: str) -> str:
    """Removes markdown formatting characters for natural voice output."""
    cleaned = re.sub(r'[*#_`>-]', '', raw_text)
    cleaned = re.sub(r'\bJarvis\b', 'Waqar', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bWaqar\b', 'وقار', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bVaqar\b', 'وقار', cleaned, flags=re.IGNORECASE)
    return " ".join(cleaned.split())

def process_and_respond(user_input: str, assistant_name: str) -> bool:
    """Processes user input, queries Gemini agent, and outputs speech."""
    if not user_input:
        return True

    if user_input.lower() in ["exit", "quit", "band karo", "stop", "khatam"]:
        farewell = f"Theek hai sir, وقار band kiya ja raha hai. Allah Hafiz!"
        print(f"[{assistant_name}]: Theek hai sir, {assistant_name} band kiya ja raha hai. Allah Hafiz!")
        speak(farewell)
        return False

    try:
        response = chat.send_message(user_input)
        response_text = response.text or "Action execute ho gaya hai."

        print(f"\n[{assistant_name} Response]:\n{response_text}")

        speech_ready_text = clean_text_for_speech(response_text)
        speak(speech_ready_text)
    except Exception as e:
        print(f"\n[Detailed Error]: {e}")
        speak("Maazrat sir, task chalane mein masla aya hai.")

    return True

def run_assistant():
    """Runs interactive assistant with selectable Keyboard or Voice input mode."""
    assistant_name = "Waqar"
    greeting_voice = "وقار active hai sir, main aapki kya madad kar sakta hoon?"
    
    print(f"[{assistant_name}]: {assistant_name} active hai sir, main aapki kya madad kar sakta hoon?")
    speak(greeting_voice)

    print("\n--- INPUT MODE SELECT ---")
    print("1: Keyboard Mode (Type karke command dein)")
    print("2: Voice Mode (Microphone se bol kar command dein)")
    mode_choice = input("Mode select karein (1 ya 2, default is 1): ").strip()

    is_voice_mode = (mode_choice == "2")

    if is_voice_mode:
        print("\n[Voice Mode Active] Mic par bolein...")
    else:
        print("\n[Keyboard Mode Active] Type karein aur Enter dabayein...")

    while True:
        try:
            if is_voice_mode:
                user_input = listen_microphone()
                if not user_input:
                    continue
                print(f"\n[Aap (Voice)]: {user_input}")
            else:
                user_input = input(f"\n[Aap likhein] (exit likhein band karne ke liye): ").strip()

            keep_running = process_and_respond(user_input, assistant_name)
            if not keep_running:
                break

        except KeyboardInterrupt:
            print(f"\n[{assistant_name}]: Assistant session ended.")
            break

if __name__ == "__main__":
    run_assistant()