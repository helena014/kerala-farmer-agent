"""
config.py — API keys and configuration
Replace the placeholder values with your real keys.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Loads from .env file

# ─── REQUIRED FOR AI FEATURES ─────────────────────────────
# Get from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

# ─── OPTIONAL (for future WhatsApp delivery) ──────────────
# Get from: https://www.twilio.com/
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# ─── APP SETTINGS ─────────────────────────────────────────
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
DEBUG    = os.getenv("DEBUG", "true").lower() == "true"
