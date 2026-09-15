import os
import sys
import re
import math
import time
import datetime
import threading
import winreg
import tkinter as tk
import customtkinter as ctk
import psutil
from PIL import Image
import pystray

# Backend agent integration
try:
    from agent_core import chat, api_key
    from voice_service import speak
except ImportError:
    chat = None
    speak = None
    api_key = "NOT SET"

ctk.set_appearance_mode("Dark")

BG_MAIN = "#0f0c1b"
BG_SIDEBAR = "#090611"
BG_CARD = "#171226"
BORDER_COLOR = "#29213d"
ACCENT_PURPLE = "#8b5cf6"
ACCENT_LIGHT = "#a78bfa"
TEXT_WHITE = "#f8fafc"
TEXT_MUTED = "#71717a"
ACCENT_GREEN = "#10b981"
ACCENT_RED = "#ef4444"

# ----------------- Windows Auto-Start Registry Utilities -----------------
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "DataNest_Assistant"

def is_autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except WindowsError:
        return False

def set_autostart(enable: bool):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_ALL_ACCESS) as key:
            if enable:
                # Agar standalone exe ho to sys.executable, warna script path
                if getattr(sys, 'frozen', False):
                    exe_path = f'"{sys.executable}" --tray'
                else:
                    exe_path = f'"{sys.executable}" "{os.path.abspath(__file__)}" --tray'
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except WindowsError:
                    pass
    except Exception as e:
        print(f"Registry Error: {e}")

class AudioEngine:
    def __init__(self, app_ref):
        self.app = app_ref
        self.is_listening = False
        self.recognizer = None
        self.microphone = None
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
        except Exception:
            pass

    def toggle(self):
        if self.is_listening:
            self.is_listening = False
            self.app.set_voice_active(False)
        else:
            if not self.recognizer:
                return
            self.is_listening = True
            self.app.set_voice_active(True)
            threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        import speech_recognition as sr
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=8)
                text = self.recognizer.recognize_google(audio, language="ur-PK")
                if text:
                    self.app.after(0, lambda: self.app.dispatch_query(text))
            except Exception:
                pass
        self.is_listening = False
        self.app.after(0, lambda: self.app.set_voice_active(False))


class DataNestAssistant(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DataNest - Waqar AI Executive")
        self.geometry("1240x800")
        self.minsize(1050, 700)
        self.configure(fg_color=BG_MAIN)

        self.audio_engine = AudioEngine(self)
        self.pulse_phase = 0
        self.nav_buttons = {}
        self.views = {}
        self.current_tab = "AI Assistant"
        self.tray_icon = None

        # Window Close event intercept (Minimize to Tray instead of terminating)
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        self._build_sidebar()
        self._build_main_stage()
        self._animate_ai_orb()
        self._start_live_telemetry()
        self._setup_system_tray()

        # Agar Windows boot se '--tray' argument ke sath chala hai to window chupayein
        if "--tray" in sys.argv:
            self.withdraw()

    # ----------------- System Tray Setup -----------------
    def _setup_system_tray(self):
        icon_path = r"C:\AI_Agent\dist\app_icon.ico"
        if not os.path.exists(icon_path):
            img = Image.new("RGBA", (64, 64), color="#8b5cf6")
        else:
            img = Image.open(icon_path)

        menu = pystray.Menu(
            pystray.MenuItem("Open Assistant", self.restore_from_tray, default=True),
            pystray.MenuItem("Exit Application", self.quit_application)
        )
        self.tray_icon = pystray.Icon("DataNest", img, "DataNest Assistant", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def minimize_to_tray(self):
        self.withdraw()

    def restore_from_tray(self, icon=None, item=None):
        self.after(0, self._show_window)

    def _show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def quit_application(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()
        sys.exit(0)

    # ----------------- UI Builders -----------------
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=BG_SIDEBAR, border_width=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=(25, 20))
        ctk.CTkLabel(
            brand_frame, text="❖ DataNest",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=TEXT_WHITE
        ).pack(anchor="w")

        menu_items = [
            ("Dashboard", "▦"),
            ("Analytics", "📈"),
            ("Performance", "⚡"),
            ("Conversions", "🔄"),
            ("Alerts", "🔔"),
            ("AI Assistant", "✨"),
            ("Settings", "⚙")
        ]

        for name, icon in menu_items:
            is_active = (name == "AI Assistant")
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}  {name}",
                anchor="w",
                height=40,
                font=ctk.CTkFont(size=13, weight="bold" if is_active else "normal"),
                fg_color=ACCENT_PURPLE if is_active else "transparent",
                text_color=TEXT_WHITE if is_active else TEXT_MUTED,
                hover_color="#21173d" if not is_active else ACCENT_PURPLE,
                corner_radius=10,
                command=lambda n=name: self.switch_tab(n)
            )
            btn.pack(fill="x", padx=14, pady=3)
            self.nav_buttons[name] = btn

        ctk.CTkLabel(
            self.sidebar, text="CHANNELS",
            font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=22, pady=(22, 6))

        for ch, icon in [("Instagram", "📸"), ("Facebook", "👥"), ("Google", "🔍")]:
            btn_ch = ctk.CTkButton(
                self.sidebar, text=f"{icon}  {ch}", anchor="w", height=30,
                font=ctk.CTkFont(size=11), fg_color="transparent", text_color=TEXT_MUTED,
                hover_color="#181329", command=lambda c=ch: self.dispatch_query(f"Open {c} on browser")
            )
            btn_ch.pack(fill="x", padx=14, pady=2)

        upgrade_box = ctk.CTkFrame(self.sidebar, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        upgrade_box.pack(side="bottom", fill="x", padx=14, pady=20)
        ctk.CTkLabel(upgrade_box, text="⚡ System Engine", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_WHITE).pack(anchor="w", padx=12, pady=(10, 2))

        self.lbl_sidebar_status = ctk.CTkLabel(
            upgrade_box, text="Model: gemini-flash-lite\nSystem: Online & Armed",
            font=ctk.CTkFont(size=10), text_color=TEXT_MUTED, justify="left"
        )
        self.lbl_sidebar_status.pack(anchor="w", padx=12, pady=(0, 10))

    def _build_main_stage(self):
        self.stage = ctk.CTkFrame(self, fg_color="transparent")
        self.stage.pack(side="right", fill="both", expand=True, padx=25, pady=20)

        top_bar = ctk.CTkFrame(self.stage, fg_color="transparent", height=45)
        top_bar.pack(fill="x", pady=(0, 15))

        self.screen_title = ctk.CTkLabel(
            top_bar, text="AI Assistant",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=TEXT_WHITE
        )
        self.screen_title.pack(side="left", padx=5)

        profile_badge = ctk.CTkFrame(top_bar, fg_color=BG_CARD, corner_radius=18, border_width=1, border_color=BORDER_COLOR)
        profile_badge.pack(side="right", padx=(10, 0))
        ctk.CTkLabel(profile_badge, text="👤 Syed Waqar", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_WHITE).pack(side="left", padx=(14, 14), pady=7)

        btn_min = ctk.CTkButton(
            top_bar, text="Tray ▾", width=70, height=36,
            fg_color="#21173d", hover_color=ACCENT_PURPLE,
            text_color=TEXT_WHITE, corner_radius=10,
            command=self.minimize_to_tray
        )
        btn_min.pack(side="right", padx=5)

        new_btn = ctk.CTkButton(
            top_bar, text="+ New Chat", width=95, height=36,
            fg_color=BG_CARD, border_width=1, border_color=BORDER_COLOR,
            text_color=TEXT_WHITE, corner_radius=10, hover_color="#271c45",
            command=self.clear_conversation
        )
        new_btn.pack(side="right", padx=5)

        self.views_container = ctk.CTkFrame(self.stage, fg_color="transparent")
        self.views_container.pack(fill="both", expand=True)
        self.views_container.grid_columnconfigure(0, weight=1)
        self.views_container.grid_rowconfigure(0, weight=1)

        self._build_dashboard_tab()
        self._build_analytics_tab()
        self._build_performance_tab()
        self._build_conversions_tab()
        self._build_alerts_tab()
        self._build_ai_tab()
        self._build_settings_tab()

        self.switch_tab("AI Assistant")

    def switch_tab(self, tab_name: str):
        self.current_tab = tab_name
        self.screen_title.configure(text=tab_name)

        for name, btn in self.nav_buttons.items():
            if name == tab_name:
                btn.configure(fg_color=ACCENT_PURPLE, text_color=TEXT_WHITE, font=ctk.CTkFont(size=13, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED, font=ctk.CTkFont(size=13, weight="normal"))

        if tab_name in self.views:
            self.views[tab_name].tkraise()

    # ----------------- Tabs -----------------
    def _build_dashboard_tab(self):
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        self.views["Dashboard"] = frame

        metrics_box = ctk.CTkFrame(frame, fg_color="transparent")
        metrics_box.pack(fill="x", pady=10)

        c1 = ctk.CTkFrame(metrics_box, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        c1.pack(side="left", fill="both", expand=True, padx=6)
        ctk.CTkLabel(c1, text="CPU USAGE", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(14, 2))
        self.dash_cpu_val = ctk.CTkLabel(c1, text="--%", font=ctk.CTkFont(size=24, weight="bold"), text_color=ACCENT_PURPLE)
        self.dash_cpu_val.pack(anchor="w", padx=16)
        self.dash_cpu_bar = ctk.CTkProgressBar(c1, progress_color=ACCENT_PURPLE, fg_color="#2b2342", height=8)
        self.dash_cpu_bar.pack(fill="x", padx=16, pady=(8, 14))

        c2 = ctk.CTkFrame(metrics_box, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        c2.pack(side="left", fill="both", expand=True, padx=6)
        ctk.CTkLabel(c2, text="RAM CONSUMPTION", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(14, 2))
        self.dash_ram_val = ctk.CTkLabel(c2, text="--%", font=ctk.CTkFont(size=24, weight="bold"), text_color="#38bdf8")
        self.dash_ram_val.pack(anchor="w", padx=16)
        self.dash_ram_bar = ctk.CTkProgressBar(c2, progress_color="#38bdf8", fg_color="#2b2342", height=8)
        self.dash_ram_bar.pack(fill="x", padx=16, pady=(8, 14))

        c3 = ctk.CTkFrame(metrics_box, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        c3.pack(side="left", fill="both", expand=True, padx=6)
        ctk.CTkLabel(c3, text="C: DRIVE STORAGE", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(14, 2))
        self.dash_disk_val = ctk.CTkLabel(c3, text="-- GB Free", font=ctk.CTkFont(size=24, weight="bold"), text_color=ACCENT_GREEN)
        self.dash_disk_val.pack(anchor="w", padx=16)
        self.dash_disk_bar = ctk.CTkProgressBar(c3, progress_color=ACCENT_GREEN, fg_color="#2b2342", height=8)
        self.dash_disk_bar.pack(fill="x", padx=16, pady=(8, 14))

        ctrl_panel = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        ctrl_panel.pack(fill="both", expand=True, padx=6, pady=15)
        ctk.CTkLabel(ctrl_panel, text="Operational Command Deck", font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_WHITE).pack(anchor="w", padx=20, pady=(15, 10))

        grid = ctk.CTkFrame(ctrl_panel, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=20, pady=10)

        quick_actions = [
            ("Play YouTube Music", "YouTube par Atif Aslam play karo"),
            ("Check Free Disk Space", "C Drive ka free space check karo"),
            ("Launch Google Chrome", "Chrome open karo"),
            ("Open Windows Notepad", "Notepad open karo"),
            ("System Performance Scan", "Full system stats check karo"),
            ("Clear Temp Files Command", "System status report banao")
        ]

        for i, (title, prompt) in enumerate(quick_actions):
            r = i // 3
            c = i % 3
            b = ctk.CTkButton(
                grid, text=f"⚡ {title}", height=45, fg_color="#21173d", hover_color=ACCENT_PURPLE,
                text_color=TEXT_WHITE, corner_radius=10, command=lambda p=prompt: self._execute_and_goto_chat(p)
            )
            b.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            grid.grid_columnconfigure(c, weight=1)

    def _build_analytics_tab(self):
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        self.views["Analytics"] = frame

        ctk.CTkLabel(frame, text="Real-Time CPU Load Distribution", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_WHITE).pack(anchor="w", padx=10, pady=5)

        chart_card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR, height=220)
        chart_card.pack(fill="x", padx=10, pady=10)
        chart_card.pack_propagate(False)

        self.canvas_chart = ctk.CTkCanvas(chart_card, bg=BG_CARD, highlightthickness=0)
        self.canvas_chart.pack(fill="both", expand=True, padx=15, pady=15)
        self.cpu_history = [20] * 35

        ctk.CTkLabel(frame, text="Multi-Core Processor Load", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_WHITE).pack(anchor="w", padx=10, pady=(15, 5))
        self.cores_scroll = ctk.CTkScrollableFrame(frame, fg_color=BG_CARD, corner_radius=14, height=180, border_width=1, border_color=BORDER_COLOR)
        self.cores_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        self.core_bars = []

        try:
            core_count = psutil.cpu_count(logical=True) or 4
            for i in range(core_count):
                row = ctk.CTkFrame(self.cores_scroll, fg_color="transparent")
                row.pack(fill="x", pady=4, padx=10)
                ctk.CTkLabel(row, text=f"Core #{i+1}", font=ctk.CTkFont(size=11), width=60, text_color=TEXT_MUTED).pack(side="left")
                bar = ctk.CTkProgressBar(row, progress_color=ACCENT_PURPLE, fg_color="#2b2342", height=8)
                bar.pack(side="left", fill="x", expand=True, padx=10)
                lbl = ctk.CTkLabel(row, text="0%", font=ctk.CTkFont(size=11), width=45, text_color=TEXT_WHITE)
                lbl.pack(side="right")
                self.core_bars.append((bar, lbl))
        except Exception:
            pass

    def _build_performance_tab(self):
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        self.views["Performance"] = frame

        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(hdr, text="Active Task & Process Monitor", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_WHITE).pack(side="left")
        ctk.CTkButton(hdr, text="↻ Refresh List", width=110, height=30, fg_color=ACCENT_PURPLE, hover_color=ACCENT_LIGHT, command=self._refresh_processes).pack(side="right")

        table_card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        table_card.pack(fill="both", expand=True, padx=10, pady=10)

        th = ctk.CTkFrame(table_card, fg_color="#201836", height=32, corner_radius=8)
        th.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(th, text="PID", font=ctk.CTkFont(size=11, weight="bold"), width=70, text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(th, text="PROCESS NAME", font=ctk.CTkFont(size=11, weight="bold"), anchor="w", text_color=TEXT_MUTED).pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkLabel(th, text="MEMORY (MB)", font=ctk.CTkFont(size=11, weight="bold"), width=120, text_color=TEXT_MUTED).pack(side="right", padx=10)

        self.proc_scroll = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self.proc_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._refresh_processes()

    def _refresh_processes(self):
        for w in self.proc_scroll.winfo_children():
            w.destroy()

        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                mem_mb = round(p.info['memory_info'].rss / (1024 * 1024), 1)
                procs.append((p.info['pid'], p.info['name'], mem_mb))
            except Exception:
                pass

        procs.sort(key=lambda x: x[2], reverse=True)
        for pid, name, mem in procs[:15]:
            r = ctk.CTkFrame(self.proc_scroll, fg_color="transparent", height=28)
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=str(pid), font=ctk.CTkFont(size=11), width=70, text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(r, text=name, font=ctk.CTkFont(size=12), anchor="w", text_color=TEXT_WHITE).pack(side="left", fill="x", expand=True, padx=10)
            ctk.CTkLabel(r, text=f"{mem} MB", font=ctk.CTkFont(size=11, weight="bold"), width=120, text_color=ACCENT_LIGHT).pack(side="right", padx=10)

    def _build_conversions_tab(self):
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        self.views["Conversions"] = frame

        ctk.CTkLabel(frame, text="Quick Utility & System Converters", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_WHITE).pack(anchor="w", padx=15, pady=10)

        c1 = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        c1.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(c1, text="Data Storage Converter (GB to MB / KB)", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_WHITE).pack(anchor="w", padx=15, pady=(12, 6))

        r1 = ctk.CTkFrame(c1, fg_color="transparent")
        r1.pack(fill="x", padx=15, pady=(0, 15))
        self.entry_gb = ctk.CTkEntry(r1, placeholder_text="Enter Gigabytes (GB)...", width=220)
        self.entry_gb.pack(side="left", padx=(0, 10))
        btn_calc = ctk.CTkButton(r1, text="Convert", width=90, fg_color=ACCENT_PURPLE, command=self._convert_storage)
        btn_calc.pack(side="left")
        self.lbl_storage_res = ctk.CTkLabel(r1, text="Result: --", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_GREEN)
        self.lbl_storage_res.pack(side="left", padx=20)

        c2 = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        c2.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(c2, text="Currency Estimator (USD to PKR)", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_WHITE).pack(anchor="w", padx=15, pady=(12, 6))

        r2 = ctk.CTkFrame(c2, fg_color="transparent")
        r2.pack(fill="x", padx=15, pady=(0, 15))
        self.entry_usd = ctk.CTkEntry(r2, placeholder_text="Enter USD ($)...", width=220)
        self.entry_usd.pack(side="left", padx=(0, 10))
        btn_curr = ctk.CTkButton(r2, text="Calculate", width=90, fg_color=ACCENT_PURPLE, command=self._convert_currency)
        btn_curr.pack(side="left")
        self.lbl_curr_res = ctk.CTkLabel(r2, text="Estimated: -- PKR", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_LIGHT)
        self.lbl_curr_res.pack(side="left", padx=20)

    def _convert_storage(self):
        try:
            val = float(self.entry_gb.get().strip())
            mb = val * 1024
            tb = val / 1024
            self.lbl_storage_res.configure(text=f"= {mb:,.1f} MB  |  {tb:.4f} TB")
        except Exception:
            self.lbl_storage_res.configure(text="Invalid numeric input!")

    def _convert_currency(self):
        try:
            val = float(self.entry_usd.get().strip())
            pkr = val * 278.5
            self.lbl_curr_res.configure(text=f"≈ {pkr:,.2f} PKR")
        except Exception:
            self.lbl_curr_res.configure(text="Invalid numeric input!")

    def _build_alerts_tab(self):
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        self.views["Alerts"] = frame

        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(hdr, text="Security & System Event Logs", font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_WHITE).pack(side="left")
        ctk.CTkButton(hdr, text="Clear Log", width=90, height=28, fg_color="#271c45", command=self._clear_alerts).pack(side="right")

        self.alerts_scroll = ctk.CTkScrollableFrame(frame, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        self.alerts_scroll.pack(fill="both", expand=True, padx=15, pady=10)

        self._add_alert_item("System Initialized", "Waqar agent running in executive isolation mode.", "INFO")
        self._add_alert_item("Tray System Active", "Background listener & quick toggle enabled.", "SUCCESS")

    def _add_alert_item(self, title, desc, level="INFO"):
        color = ACCENT_PURPLE
        if level in ["SECURE", "SUCCESS"]:
            color = ACCENT_GREEN
        elif level in ["WARN", "ALERT"]:
            color = ACCENT_RED

        card = ctk.CTkFrame(self.alerts_scroll, fg_color="#1d1630", corner_radius=10)
        card.pack(fill="x", pady=4, padx=5)
        t = datetime.datetime.now().strftime("%H:%M:%S")
        ctk.CTkLabel(card, text=f"[{level}] {title} • {t}", font=ctk.CTkFont(size=11, weight="bold"), text_color=color).pack(anchor="w", padx=12, pady=(6, 2))
        ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(0, 6))

    def _clear_alerts(self):
        for w in self.alerts_scroll.winfo_children():
            w.destroy()

    def _build_ai_tab(self):
        parent = ctk.CTkFrame(self.views_container, fg_color="transparent")
        parent.grid(row=0, column=0, sticky="nsew")
        self.views["AI Assistant"] = parent

        self.welcome_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.welcome_frame.pack(pady=(15, 5))

        self.orb_canvas = ctk.CTkCanvas(self.welcome_frame, width=80, height=80, bg=BG_MAIN, highlightthickness=0)
        self.orb_canvas.pack(pady=(0, 8))

        self.hero_text = ctk.CTkLabel(self.welcome_frame, text="What can I help with?", font=ctk.CTkFont(family="Inter", size=22, weight="bold"), text_color=TEXT_WHITE)
        self.hero_text.pack()

        self.chat_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        bottom_dock_wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        bottom_dock_wrapper.pack(side="bottom", fill="x", pady=(8, 10))

        self.input_card = ctk.CTkFrame(bottom_dock_wrapper, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=BORDER_COLOR)
        self.input_card.pack(fill="x", padx=30)

        self.input_text = ctk.CTkTextbox(
            self.input_card, fg_color="transparent", text_color=TEXT_WHITE,
            font=ctk.CTkFont(size=13), border_width=0, wrap="word", height=50
        )
        self.input_text.pack(fill="x", padx=14, pady=(8, 0))
        self.input_text.insert("1.0", "Ask anything AI assistant...")
        self.input_text.bind("<FocusIn>", self._clear_placeholder)
        self.input_text.bind("<Return>", self._handle_enter)

        dock_actions = ctk.CTkFrame(self.input_card, fg_color="transparent", height=36)
        dock_actions.pack(fill="x", side="bottom", padx=12, pady=6)

        ctk.CTkLabel(dock_actions, text="➕   📎   🖼", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(side="left", padx=5)

        self.send_btn = ctk.CTkButton(
            dock_actions, text="▲", width=34, height=34,
            corner_radius=17, fg_color=ACCENT_PURPLE,
            hover_color=ACCENT_LIGHT, text_color=TEXT_WHITE,
            command=self._send_from_box
        )
        self.send_btn.pack(side="right", padx=(6, 0))

        self.mic_btn = ctk.CTkButton(
            dock_actions, text="🎙", width=34, height=34,
            corner_radius=17, fg_color="#2b2342",
            hover_color="#3d325c", text_color=TEXT_WHITE,
            command=self.audio_engine.toggle
        )
        self.mic_btn.pack(side="right", padx=4)

        self.chips_row = ctk.CTkFrame(parent, fg_color="transparent")
        self.chips_row.pack(side="bottom", pady=(0, 4))

        presets = [
            ("Play Music", "YouTube par Atif Aslam play karo"),
            ("System Health", "CPU aur RAM usage batao"),
            ("Google Search", "Google par Python tips search karo")
        ]

        for title, prompt in presets:
            btn_card = ctk.CTkButton(
                self.chips_row, text=title, font=ctk.CTkFont(size=11),
                fg_color=BG_CARD, hover_color="#21173d", text_color=TEXT_MUTED,
                border_width=1, border_color=BORDER_COLOR, corner_radius=10,
                width=160, height=34,
                command=lambda p=prompt: self.dispatch_query(p)
            )
            btn_card.pack(side="left", padx=6)

    def _clear_placeholder(self, event):
        if "Ask anything" in self.input_text.get("1.0", "end"):
            self.input_text.delete("1.0", "end")

    def _handle_enter(self, event):
        if not event.state & 0x1:
            self._send_from_box()
            return "break"

    def _send_from_box(self):
        text = self.input_text.get("1.0", "end").strip()
        if text and "Ask anything" not in text:
            self.input_text.delete("1.0", "end")
            self.dispatch_query(text)

    def set_voice_active(self, active: bool):
        if active:
            self.mic_btn.configure(fg_color=ACCENT_RED)
            self.hero_text.configure(text="Listening to voice...")
        else:
            self.mic_btn.configure(fg_color="#2b2342")
            self.hero_text.configure(text="What can I help with?")

    def _animate_ai_orb(self):
        self.orb_canvas.delete("all")
        self.pulse_phase += 0.08
        r = 24 + math.sin(self.pulse_phase) * 3

        self.orb_canvas.create_oval(40 - r - 6, 40 - r - 6, 40 + r + 6, 40 + r + 6, fill="#1c133b", outline="")
        self.orb_canvas.create_oval(40 - r, 40 - r, 40 + r, 40 + r, fill=ACCENT_PURPLE, outline="#c4b5fd", width=1.5)
        self.orb_canvas.create_oval(37, 37, 43, 43, fill="#ffffff", outline="")

        self.after(40, self._animate_ai_orb)

    def append_chat_bubble(self, sender: str, text: str):
        self.welcome_frame.pack_forget()
        self.chips_row.pack_forget()
        self.chat_scroll.pack(side="top", fill="both", expand=True, padx=25, pady=(5, 10))

        is_user = (sender.lower() == "user")
        bubble_frame = ctk.CTkFrame(
            self.chat_scroll, fg_color="#1f1a32" if is_user else BG_CARD,
            corner_radius=12, border_width=1, border_color=BORDER_COLOR
        )
        bubble_frame.pack(fill="x", pady=6, padx=8, anchor="e" if is_user else "w")

        title_lbl = ctk.CTkLabel(
            bubble_frame, text="You" if is_user else "Waqar AI",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=ACCENT_LIGHT if not is_user else TEXT_WHITE
        )
        title_lbl.pack(anchor="w", padx=12, pady=(6, 2))

        msg_lbl = ctk.CTkLabel(bubble_frame, text=text, font=ctk.CTkFont(size=13), text_color=TEXT_WHITE, wraplength=720, justify="left")
        msg_lbl.pack(anchor="w", padx=12, pady=(0, 8))

        self.after(50, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))

    def dispatch_query(self, user_text: str):
        self.append_chat_bubble("user", user_text)

        def worker():
            if chat:
                try:
                    resp = chat.send_message(user_text)
                    ans = resp.text or "Action completed."
                except Exception as e:
                    ans = f"Execution error: {e}"
            else:
                time.sleep(1)
                ans = f"Processed: '{user_text}'."

            self.after(0, lambda: self.append_chat_bubble("waqar", ans))
            if speak:
                cleaned = re.sub(r'[*#_`>-]', '', ans)
                speak(cleaned)

        threading.Thread(target=worker, daemon=True).start()

    def _execute_and_goto_chat(self, prompt):
        self.switch_tab("AI Assistant")
        self.dispatch_query(prompt)

    def clear_conversation(self):
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()
        self.chat_scroll.pack_forget()
        self.welcome_frame.pack(pady=(15, 5))
        self.chips_row.pack(side="bottom", pady=(0, 4))
        self.hero_text.configure(text="What can I help with?")

    # ----------------- Settings & Auto-Start Configuration -----------------
    def _build_settings_tab(self):
        frame = ctk.CTkFrame(self.views_container, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        self.views["Settings"] = frame

        ctk.CTkLabel(frame, text="Preferences & Engine Configuration", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_WHITE).pack(anchor="w", padx=15, pady=10)

        c = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        c.pack(fill="x", padx=15, pady=8)

        # 1. Windows Auto-Start Toggle
        r_boot = ctk.CTkFrame(c, fg_color="transparent")
        r_boot.pack(fill="x", padx=15, pady=12)
        ctk.CTkLabel(r_boot, text="Start on Windows Boot (Silent Tray)", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_WHITE).pack(side="left")
        self.switch_autostart = ctk.CTkSwitch(r_boot, text="Enabled", progress_color=ACCENT_PURPLE, command=self._toggle_autostart)
        if is_autostart_enabled():
            self.switch_autostart.select()
        else:
            self.switch_autostart.deselect()
        self.switch_autostart.pack(side="right")

        # 2. Text-to-Speech Toggle
        r1 = ctk.CTkFrame(c, fg_color="transparent")
        r1.pack(fill="x", padx=15, pady=12)
        ctk.CTkLabel(r1, text="Text-to-Speech Audio Feedback", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_WHITE).pack(side="left")
        self.switch_tts = ctk.CTkSwitch(r1, text="Active", progress_color=ACCENT_PURPLE)
        self.switch_tts.select()
        self.switch_tts.pack(side="right")

        # 3. Model info
        r2 = ctk.CTkFrame(c, fg_color="transparent")
        r2.pack(fill="x", padx=15, pady=12)
        ctk.CTkLabel(r2, text="Active LLM Architecture", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_WHITE).pack(side="left")
        ctk.CTkLabel(r2, text="gemini-flash-lite-latest (Function Calling)", font=ctk.CTkFont(size=11), text_color=ACCENT_LIGHT).pack(side="right")

        # 4. Key Status
        r3 = ctk.CTkFrame(c, fg_color="transparent")
        r3.pack(fill="x", padx=15, pady=12)
        ctk.CTkLabel(r3, text="API Security Status", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_WHITE).pack(side="left")
        masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "Verified"
        ctk.CTkLabel(r3, text=f"Key: {masked_key}", font=ctk.CTkFont(size=11), text_color=ACCENT_GREEN).pack(side="right")

    def _toggle_autostart(self):
        enabled = (self.switch_autostart.get() == 1)
        set_autostart(enabled)
        status_str = "Enabled" if enabled else "Disabled"
        self._add_alert_item("Auto-Start Changed", f"Windows boot launch {status_str}.", "INFO")

    # ----------------- Background Telemetry Loop -----------------
    def _start_live_telemetry(self):
        def loop():
            while True:
                try:
                    cpu = psutil.cpu_percent(interval=1)
                    ram = psutil.virtual_memory().percent
                    disk = psutil.disk_usage('C:\\')
                    free_gb = round(disk.free / (1024**3), 1)

                    self.dash_cpu_val.configure(text=f"{cpu}%")
                    self.dash_cpu_bar.set(cpu / 100.0)

                    self.dash_ram_val.configure(text=f"{ram}%")
                    self.dash_ram_bar.set(ram / 100.0)

                    self.dash_disk_val.configure(text=f"{free_gb} GB Free")
                    self.dash_disk_bar.set(disk.percent / 100.0)

                    self.cpu_history.pop(0)
                    self.cpu_history.append(cpu)
                    self._draw_analytics_chart()

                    per_core = psutil.cpu_percent(percpu=True)
                    for idx, val in enumerate(per_core):
                        if idx < len(self.core_bars):
                            bar, lbl = self.core_bars[idx]
                            bar.set(val / 100.0)
                            lbl.configure(text=f"{int(val)}%")
                except Exception:
                    pass
                time.sleep(1.5)

        threading.Thread(target=loop, daemon=True).start()

    def _draw_analytics_chart(self):
        try:
            self.canvas_chart.delete("all")
            w = self.canvas_chart.winfo_width() or 680
            h = self.canvas_chart.winfo_height() or 180

            pts = []
            step = w / (len(self.cpu_history) - 1)
            for i, val in enumerate(self.cpu_history):
                x = i * step
                y = h - (val / 100.0 * (h - 20)) - 10
                pts.append((x, y))

            for i in range(len(pts) - 1):
                self.canvas_chart.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], fill=ACCENT_PURPLE, width=2.5)

            lx, ly = pts[-1]
            self.canvas_chart.create_oval(lx - 4, ly - 4, lx + 4, ly + 4, fill=ACCENT_LIGHT, outline="")
        except Exception:
            pass

if __name__ == "__main__":
    app = DataNestAssistant()
    app.mainloop()