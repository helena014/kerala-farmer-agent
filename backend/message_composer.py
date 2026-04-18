"""
message_composer.py
Uses Google Gemini API to compose Malayalam advisory messages.
Falls back to a template if no API key is set.
"""


import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def _get_gemini_url():
    api_key = os.getenv("GEMINI_API_KEY", "")
    return f"{GEMINI_BASE}?key={api_key}", api_key


async def compose_advisory_message(farmer: dict, prices: dict, weather: dict, pest: dict) -> str:
    """Generate a Malayalam WhatsApp advisory using Gemini AI."""
    gemini_url, api_key = _get_gemini_url()
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        return _template_message(farmer, prices, weather, pest)


    price_str = ",".join([
        f"{m['mandi']}: ₹{m['price']:,}/quintal ({m['trend']})"
        for m in prices.get("mandis", [])
    ])
    weather_str = ",".join([
        f"{d['day']} {d['icon']} {d['temp']} {d['rain_pct']}% rain"
        for d in weather.get("forecast", [])[:3]
    ])


    prompt = f"""You are Kerala Krishi Advisory Agent. Write a WhatsApp morning advisory for this farmer.


Farmer: {farmer['name']}, Crop: {farmer['crop']}, District: {farmer['district']}, Land: {farmer['land']} acres


Market prices (Agmarknet): {price_str}
Sell advice: {prices.get('sell_advice', '')}


Weather (5-day IMD forecast): {weather_str}
Weather tip: {weather.get('action_tip', '')}


Pest/Disease bulletin: {pest.get('title', '')} — {pest.get('action', '')}


Rules:
1. Write ENTIRELY in Malayalam script (Unicode)
2. Keep under 120 words
3. Use *bold* markers around prices and key actions
4. Order: 🌅 greeting → price + sell/wait advice → weather tip → pest tip → sign-off
5. Start: "🌅 ഗുഡ് മോർണിംഗ്, {farmer['name']} ജി!"
6. End: "ഏതെങ്കിലും സംശയം ഉണ്ടെങ്കിൽ reply ചെയ്യൂ 🙏"
7. Warm, friendly tone. 8th-grade reading level.


Write only the message — no preamble."""


    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(gemini_url, json={"contents": [{"parts": [{"text": prompt}]}]})
            data = resp.json()
            if "error" in data:
                print(f"Gemini error: {data['error']['message']}")
                return _template_message(farmer, prices, weather, pest)
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini call failed: {e}")
        return _template_message(farmer, prices, weather, pest)




def _template_message(farmer: dict, prices: dict, weather: dict, pest: dict) -> str:
    """Fallback template message (no API key needed)."""
    mandis = prices.get("mandis", [])
    price_lines = "\n".join([
        f"• {m['mandi']}: ₹{m['price']:,}/quintal {'↑' if m['trend']=='up' else '↓' if m['trend']=='down' else '→'}"
        for m in mandis
    ])
    trend = prices.get("trend", "flat")
    sell  = "ഈ ആഴ്ച വിൽക്കാൻ നല്ലതാണ്! 🟢" if trend == "up" else "കൂടുതൽ കാത്തിരിക്കുക. 🔴" if trend == "down" else "വില സ്ഥിരമാണ്. →"


    fcst = weather.get("forecast", [])
    rain_days = [d["day"] for d in fcst if d["rain_pct"] > 50]
    weather_tip = f"{', '.join(rain_days)}-ൽ ശക്തമായ മഴ. ഉണക്കൽ/കൊയ്ത്ത് നേരത്തെ ചെയ്യുക! ⚠️" if rain_days else "ഈ ആഴ്ച നല്ല കാലാവസ്ഥ. ☀️"


    pest_tip = pest.get("title", "No active alerts")


    from datetime import datetime
    today = datetime.now().strftime("%d/%m/%Y")


    return f"""🌅 ഗുഡ് മോർണിംഗ്, {farmer['name']} ജി!
Kerala Krishi Agent — {today}


📈 *{farmer['crop']} വില ({farmer['district']}):*
{price_lines}


💡 *ഉപദേശം:* {sell}
{prices.get('sell_advice', '')}


🌤️ *കാലാവസ്ഥ:*
{weather_tip}


🐛 *കൃഷി ജാഗ്രത:*
{pest_tip}
{pest.get('action', '')}


ഏതെങ്കിലും സംശയം ഉണ്ടെങ്കിൽ reply ചെയ്യൂ 🙏"""


