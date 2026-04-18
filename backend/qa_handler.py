"""
qa_handler.py
Handles reactive Q&A from farmers using Gemini AI.
Answers ANY question in Malayalam using Gemini 2.0 Flash.
"""

import httpx
import os
from dotenv import load_dotenv
from data_fetcher import PEST_DATA, BASE_PRICES

load_dotenv()

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


async def answer_farmer_question(farmer: dict, question: str, conversation_history: list) -> str:
    """Answer a farmer's follow-up question using Gemini AI."""

    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        return _keyword_answer(question, farmer)

    pest       = PEST_DATA.get(farmer["crop"], {})
    crop_prices = BASE_PRICES.get(farmer["crop"], {})
    base_price  = crop_prices.get(farmer["district"], crop_prices.get("default", "N/A"))

    system_text = (
        f"നീ Kerala Krishi Advisory Agent ആണ്. "
        f"Kerala കർഷകർക്ക് കൃഷി, വില, കാലാവസ്ഥ, കീടം എന്നിവയെ കുറിച്ച് സഹായം ചെയ്യുക. "
        f"എല്ലാ മറുപടിയും Malayalam-ൽ (Unicode script) ആയിരിക്കണം. "
        f"ഉത്തരം ചെറുതും practical-ഉം warm-ഉം ആയിരിക്കണം. "
        f"Maximum 80 words. 8th grade reading level. "
        f"Farmer details: Name={farmer['name']}, Crop={farmer['crop']}, "
        f"District={farmer['district']}, Land={farmer['land']} acres. "
        f"Today's approximate price: Rs.{base_price}/quintal. "
        f"Active pest alert: {pest.get('title', 'None')} — {pest.get('action', '')}. "
        f"Key advice words ഉണ്ടെങ്കിൽ *bold* ചെയ്യുക. Emojis ഉപയോഗിക്കുക."
    )

    # Build conversation contents
    contents = []

    # Add previous conversation turns
    for msg in (conversation_history or []):
        role = msg.get("role", "user")
        text = msg.get("text", "")
        if role == "assistant":
            role = "model"
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})

    # Add current question
    contents.append({
        "role": "user",
        "parts": [{"text": f"കർഷകൻ ചോദിക്കുന്നു: \"{question}\"\nMalayalam-ൽ മറുപടി പറയുക."}]
    })

    payload = {
        "system_instruction": {"parts": [{"text": system_text}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300,
        }
    }

    url = f"{GEMINI_URL}?key={api_key}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            data = resp.json()

            if "error" in data:
                print(f"Gemini Q&A error: {data['error']['message']}")
                return _keyword_answer(question, farmer)

            reply = data["candidates"][0]["content"]["parts"][0]["text"]
            return reply.strip()

    except Exception as e:
        print(f"Q&A Gemini exception: {e}")
        return _keyword_answer(question, farmer)


def _keyword_answer(question: str, farmer: dict) -> str:
    """Fallback when Gemini is unavailable."""
    q = question.lower()

    if any(w in q for w in ["വില", "price", "rate", "cost"]):
        return f"📊 ഇന്ന് {farmer['crop']} വില ഏകദേശം ₹{BASE_PRICES.get(farmer['crop'], {}).get(farmer['district'], BASE_PRICES.get(farmer['crop'], {}).get('default', 'N/A'))}/quintal ആണ്. Advisory message-ൽ exact mandi prices കാണാം."

    if any(w in q for w in ["sell", "വിൽക്ക", "വിൽക്കണോ"]):
        return "💰 Price trend ↑ ആണെങ്കിൽ *ഈ ആഴ്ച വിൽക്കാം*. ↓ ആണെങ്കിൽ കുറച്ചു ദിവസം കൂടി *കാത്തിരിക്കുക*."

    if any(w in q for w in ["മഴ", "rain", "weather", "കാലാവസ്ഥ"]):
        return "🌧️ IMD forecast അനുസരിച്ച് ഈ ആഴ്ച മഴ സാധ്യതയുണ്ട്. *ഉണക്കൽ/കൊയ്ത്ത് നേരത്തെ ആരംഭിക്കുക.*"

    if any(w in q for w in ["കീട", "pest", "disease", "spray", "രോഗം"]):
        pest = PEST_DATA.get(farmer["crop"], {})
        return f"🐛 {pest.get('title', 'No active alerts')}.\n*Action:* {pest.get('action', 'Regular scouting continue ചെയ്യുക.')}"

    if any(w in q for w in ["കൊപ്ര", "copra", "dry", "ഉണക്ക"]):
        return "🥥 Copra ഉണ്ടാക്കാൻ 3–4 ദിവസം continuous sunshine വേണം. *Rain forecast ഇല്ലാത്ത ദിവസം ആരംഭിക്കുക.* Moisture 6%-ൽ കുറഞ്ഞ ഉണ്ടെങ്കിൽ better price കിട്ടും."

    if any(w in q for w in ["fertilizer", "വളം", "compost"]):
        return "🌱 Kerala Agricultural University guidelines follow ചെയ്യുക. *Monsoon-നു മുൻപ് organic matter* soil-ൽ add ചെയ്യുക."

    return (
        f"🤖 നിങ്ങളുടെ ചോദ്യത്തിന് ഉത്തരം കണ്ടെത്തുന്നു...\n\n"
        f"ദയവായി ഇതിൽ ഒന്ന് ചോദിക്കുക:\n"
        f"• വില (price)\n• കൃഷി (farming)\n• കീടം (pest)\n• കാലാവസ്ഥ (weather)\n• spray"
    )