import os

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

VEXA_API_KEY = os.getenv("VEXA_API_KEY", "").strip()
BASE_URL = "https://api.cloud.vexa.ai"


def entrar_a_reunion(meeting_code: str) -> bool:
    if not VEXA_API_KEY:
        print("[Vexa] Falta VEXA_API_KEY; no puedo unirme al Meet.")
        return False

    url = f"{BASE_URL}/bots"
    headers = {
        "Authorization": f"Bearer {VEXA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "platform": "google_meet",
        "native_meeting_id": meeting_code,
        "recording_enabled": True,
        "transcribe_enabled": True,
        "transcription_tier": "realtime",
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code not in (200, 201):
            print(f"[Vexa] HTTP {res.status_code}: respuesta rechazada (sin secretos).")
        return res.status_code in (200, 201)
    except Exception as error:
        print(f"[Vexa] Error de red: {type(error).__name__}")
        return False
