from instagrapi import Client
from pathlib import Path
import getpass
import os

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

username = input("Instagram username: ").strip()
password = getpass.getpass("Instagram password: ")

session_file = SESSIONS_DIR / f"session_{username}.json"

cl = Client()

# IMPORTANT: device consistency
cl.set_device({
    "app_version": "269.0.0.18.75",
    "android_version": 26,
    "android_release": "8.0.0",
    "dpi": "480dpi",
    "resolution": "1080x1920",
    "manufacturer": "Samsung",
    "device": "SM-G960F",
    "model": "Galaxy S9",
    "cpu": "samsungexynos9810"
})

cl.login(username, password)
cl.dump_settings(session_file)

print(f"\n✅ Session created successfully")
print(f"📁 Saved at: {session_file.resolve()}")
