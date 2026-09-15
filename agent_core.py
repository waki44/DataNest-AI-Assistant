import os
import json
import time
import subprocess
import urllib.parse
import urllib.request
import re
import psutil
import pyautogui
from google import genai
from google.genai import types

CONFIG_FILE = "config.json"

def get_api_key() -> str:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                key = data.get("GEMINI_API_KEY", "").strip()
                if key:
                    return key
        except Exception:
            pass

    print("--- FIRST TIME SETUP ---")
    entered_key = input("Enter your Gemini API Key: ").strip()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"GEMINI_API_KEY": entered_key}, f, indent=4)
    return entered_key

api_key = get_api_key()
client = genai.Client(api_key=api_key)

# ---------------------------------------------------------
# Safe Tools (Direct Execution)
# ---------------------------------------------------------

def search_google(query: str) -> str:
    """Performs a Google web search and launches results in default browser."""
    clean_query = urllib.parse.quote(query.strip())
    url = f"https://www.google.com/search?q={clean_query}"
    os.system(f'start "" "{url}"')
    return f"Google par '{query}' search open kar diya gaya hai."

def play_youtube(topic_or_song: str) -> str:
    """
    Directly extracts the exact video link and plays it in the browser,
    triggering autoplay automatically.
    """
    clean_query = topic_or_song.strip()
    video_url = None
    title = clean_query

    # Method 1: yt-dlp engine se direct video ID fetch karna (Fastest & Accurate)
    try:
        import yt_dlp
        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch1'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{clean_query}", download=False)
            if 'entries' in info and len(info['entries']) > 0:
                video_url = info['entries'][0].get('webpage_url')
                title = info['entries'][0].get('title', clean_query)
    except Exception:
        pass

    # Method 2: Fallback direct regex scrape
    if not video_url:
        try:
            query_encoded = urllib.parse.quote(clean_query)
            format_url = f"https://www.youtube.com/results?search_query={query_encoded}"
            req = urllib.request.Request(
                format_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            html_content = urllib.request.urlopen(req, timeout=4).read().decode('utf-8')
            search_results = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", html_content)
            if search_results:
                video_url = f"https://www.youtube.com/watch?v={search_results[0]}"
        except Exception:
            pass

    # Method 3: Ultimate fallback
    if not video_url:
        video_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean_query)}"

    # Launch video directly in Windows default browser
    os.system(f'start "" "{video_url}"')

    # Browser launch hone ka wait aur video focus/play command
    time.sleep(3.5)
    pyautogui.press('k')  # Universal YouTube shortcut to Play/Unpause video

    return f"YouTube par '{title}' direct open aur play kar diya gaya hai."

def get_system_stats() -> str:
    """Returns live CPU, RAM, and Disk free metrics."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')
    return f"CPU usage {cpu}%, RAM {ram.percent}%, C Drive free space {round(disk.free / (1024**3), 1)} GB."

def open_application(app_name: str) -> str:
    """Opens generic applications like calculator, notepad, chrome."""
    try:
        os.system(f"start {app_name}")
        return f"{app_name} open ho gaya hai."
    except Exception as e:
        return f"App open karne mein error: {e}"

def close_application(app_name: str) -> str:
    """Closes non-critical running process."""
    process = app_name.lower().strip()
    if not process.endswith(".exe"):
        process += ".exe"
    try:
        subprocess.run(["taskkill", "/F", "/IM", process], capture_output=True, text=True)
        return f"{process} close kar diya gaya hai."
    except Exception as e:
        return f"Process close error: {e}"

# ---------------------------------------------------------
# Critical Operations (Confirmation Required)
# ---------------------------------------------------------

def execute_delete_file(file_path: str) -> str:
    """Deletes a local file after user confirmation."""
    if os.path.exists(file_path):
        os.remove(file_path)
        return f"File '{file_path}' delete kar di gayi hai."
    return f"File '{file_path}' nahi mili."

def execute_send_message(platform: str, recipient: str, message: str) -> str:
    """Executes sending external communications after user confirmation."""
    if platform.lower() == "whatsapp":
        encoded = urllib.parse.quote(message)
        url = f"https://web.whatsapp.com/send?text={encoded}"
        os.system(f'start "" "{url}"')
        return f"WhatsApp par {recipient} ke liye message load kar diya gaya hai."
    return f"{platform} action ready."

def execute_system_command(command: str) -> str:
    """Executes shell-level administrative actions after confirmation."""
    subprocess.run(command, shell=True)
    return "Administrative command execute ho chuki hai."

# ---------------------------------------------------------
# Agent Configuration
# ---------------------------------------------------------

chat = client.chats.create(
    model="gemini-flash-lite-latest",
    config=types.GenerateContentConfig(
        system_instruction=(
            "Your name is Waqar. You are an executive desktop AI assistant. "
            "STRICT RULES FOR PRIVACY & SAFETY: "
            "1. NEVER expose credentials, tokens, or private personal data. "
            "2. SAFE ACTIONS: Opening apps, closing apps, checking performance, searching Google, and playing YouTube videos. Execute these immediately every single time. "
            "3. SENSITIVE ACTIONS: Deleting files, sending WhatsApp/emails, or running system commands. For these, ask for confirmation first ('Kya main yeh send/delete kar doon?'). "
            "4. When the user asks to play a song, track, or video on YouTube, immediately call 'play_youtube'. "
            "5. When the user asks to search on Google, immediately call 'search_google'. "
            "6. Always respond in friendly, short Roman Urdu."
        ),
        tools=[
            search_google,
            play_youtube,
            get_system_stats,
            open_application,
            close_application,
            execute_delete_file,
            execute_send_message,
            execute_system_command
        ]
    )
)