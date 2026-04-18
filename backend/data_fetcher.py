"""
data_fetcher.py
Simulates Agmarknet API, IMD Weather API, and Kerala Agri Dept bulletin scraping.
In production: replace the SIMULATED blocks with real HTTP calls.
"""

import random
from datetime import datetime, timedelta

# ──────────────────────────────────────────────────────────
# MARKET PRICES (simulated Agmarknet)
# ──────────────────────────────────────────────────────────
BASE_PRICES = {
    "Rice":       {"Palakkad": 2240, "Thrissur": 2180, "Wayanad": 2160, "Ernakulam": 2200,
                   "Malappuram": 2190, "Kozhikode": 2175, "Kannur": 2210, "default": 2200},
    "Coconut":    {"Thrissur": 2840, "Ernakulam": 2760, "Kozhikode": 2810, "Palakkad": 2800,
                   "Kannur": 2750, "Wayanad": 2700, "default": 2780},
    "Pepper":     {"Wayanad": 62400, "Kannur": 61500, "Idukki": 63200, "Ernakulam": 61900,
                   "Malappuram": 62100, "default": 62000},
    "Banana":     {"Ernakulam": 1850, "Palakkad": 1780, "Kozhikode": 1900, "Thrissur": 1860,
                   "Wayanad": 1830, "default": 1820},
    "Ginger":     {"Kozhikode": 14200, "Malappuram": 13800, "Wayanad": 13500, "Thrissur": 14100,
                   "Ernakulam": 14300, "default": 14000},
    "Rubber":     {"Kottayam": 18500, "Ernakulam": 18200, "default": 18300},
    "Tapioca":    {"Thiruvananthapuram": 980, "Kollam": 960, "default": 970},
    "Vegetables": {"Ernakulam": 2400, "Thrissur": 2350, "default": 2300},
}

MANDIS = {
    "Palakkad":  ["Palakkad Mandi", "Ottapalam Mandi", "Shoranur Mandi"],
    "Thrissur":  ["Thrissur Mandi", "Chalakudy Mandi", "Irinjalakuda Mandi"],
    "Wayanad":   ["Kalpetta Mandi", "Mananthavady Mandi", "Sulthan Bathery Mandi"],
    "Ernakulam": ["Ernakulam Mandi", "Angamaly Mandi", "Perumbavoor Mandi"],
    "Kozhikode": ["Kozhikode Mandi", "Vadakara Mandi", "Feroke Mandi"],
    "Kannur":    ["Kannur Mandi", "Thalassery Mandi"],
    "Malappuram":["Malappuram Mandi", "Tirur Mandi"],
    "Kottayam":  ["Kottayam Mandi", "Changanacherry Mandi"],
}

def _trend():
    r = random.random()
    if r < 0.45: return "up"
    if r < 0.75: return "down"
    return "flat"

async def fetch_market_prices(crop: str, district: str) -> dict:
    """
    SIMULATED Agmarknet API call.
    Real API: https://agmarknet.gov.in/
    """
    crop_prices = BASE_PRICES.get(crop, BASE_PRICES["Rice"])
    base = crop_prices.get(district, crop_prices["default"])
    mandis = MANDIS.get(district, [f"{district} Mandi"])[:3]

    rows = []
    for mandi in mandis:
        variation = random.randint(-150, 200)
        price = base + variation
        rows.append({
            "mandi":  mandi,
            "price":  price,
            "trend":  _trend(),
            "unit":   "₹/quintal",
        })

    # 7-day history for trend chart
    history = []
    p = base
    for i in range(7):
        p += random.randint(-80, 100)
        history.append({
            "day":   (datetime.now() - timedelta(days=6-i)).strftime("%d %b"),
            "price": max(p, base - 500),
        })

    overall_trend = rows[0]["trend"] if rows else "flat"
    sell_advice = (
        "ഈ ആഴ്ച വിൽക്കാൻ **നല്ലതാണ്**. വില ഉയർന്നുകൊണ്ടിരിക്കുകയാണ്."
        if overall_trend == "up"
        else "കുറച്ചുദിവസം **കൂടി കാത്തിരിക്കുക**. വില ഇറങ്ങിക്കൊണ്ടിരിക്കുകയാണ്."
        if overall_trend == "down"
        else "വില **സ്ഥിരമാണ്**. ഇപ്പോൾ വിൽക്കാം."
    )

    return {
        "crop":        crop,
        "district":    district,
        "mandis":      rows,
        "trend":       overall_trend,
        "sell_advice": sell_advice,
        "history":     history,
        "source":      "Agmarknet (simulated)",
        "fetched_at":  datetime.now().isoformat(),
    }


# ──────────────────────────────────────────────────────────
# WEATHER (simulated IMD API)
# ──────────────────────────────────────────────────────────
WEATHER_PATTERNS = {
    "Wayanad":    {"rain_chance": 70, "base_temp": 26},
    "Idukki":     {"rain_chance": 65, "base_temp": 24},
    "Palakkad":   {"rain_chance": 30, "base_temp": 34},
    "Thrissur":   {"rain_chance": 45, "base_temp": 31},
    "Ernakulam":  {"rain_chance": 50, "base_temp": 30},
    "Kozhikode":  {"rain_chance": 55, "base_temp": 29},
    "Kannur":     {"rain_chance": 55, "base_temp": 29},
    "Malappuram": {"rain_chance": 50, "base_temp": 31},
    "default":    {"rain_chance": 45, "base_temp": 30},
}

ICONS = {(True, True): "⛈️", (True, False): "🌧️", (False, True): "⛅", (False, False): "☀️"}

async def fetch_weather(district: str) -> dict:
    """SIMULATED IMD weather forecast."""
    pat = WEATHER_PATTERNS.get(district, WEATHER_PATTERNS["default"])
    days = []
    base_rain = pat["rain_chance"]
    base_temp = pat["base_temp"]
    day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    for i in range(5):
        rain_pct = max(0, min(100, base_rain + random.randint(-20, 20)))
        temp     = base_temp + random.randint(-2, 3)
        heavy    = rain_pct > 60
        rainy    = rain_pct > 30
        day_offset = datetime.now() + timedelta(days=i)
        days.append({
            "day":       day_names[day_offset.weekday()],
            "date":      day_offset.strftime("%d %b"),
            "icon":      ICONS[(heavy, rainy and not heavy)],
            "temp":      f"{temp}°C",
            "rain_pct":  rain_pct,
            "condition": "Heavy Rain" if heavy else "Rain" if rainy else "Cloudy" if rain_pct > 15 else "Sunny",
        })

    rain_days = [d for d in days if d["rain_pct"] > 40]
    action = ""
    if rain_days:
        action = f"{rain_days[0]['day']}-ൽ മഴ പ്രതീക്ഷിക്കുന്നു. ഉണക്കൽ/കൊയ്ത്ത് നേരത്തെ ആരംഭിക്കുക."
    else:
        action = "ഈ ആഴ്ച നല്ല കാലാവസ്ഥ. കൊയ്ത്ത്/ഉണക്കൽ ആരംഭിക്കാൻ അനുകൂലമാണ്."

    return {
        "district":   district,
        "forecast":   days,
        "action_tip": action,
        "source":     "IMD (simulated)",
        "fetched_at": datetime.now().isoformat(),
    }


# ──────────────────────────────────────────────────────────
# PEST / DISEASE BULLETINS (simulated Kerala Agri Dept)
# ──────────────────────────────────────────────────────────
PEST_DATA = {
    "Rice": {
        "title": "🚨 Brown Plant Hopper (BPH) Alert",
        "severity": "high",
        "symptoms": "ഇലകൾ മഞ്ഞനിറമാകുന്നു; ചെടിയുടെ ചുവടുഭാഗം കരുകൊള്ളുന്നു.",
        "action": "10 insects/hill കണ്ടാൽ Buprofezin 25% SC (1ml/litre water) spray ചെയ്യുക. Yellow sticky traps ഉപയോഗിക്കുക.",
        "prevention": "Over-fertilisation ഒഴിവാക്കുക. Field drainage ഉറപ്പ് വരുത്തുക.",
    },
    "Coconut": {
        "title": "⚠️ Rhinoceros Beetle (Oryctes rhinoceros)",
        "severity": "medium",
        "symptoms": "Trunk-ൽ ദ്വാരങ്ങൾ; crown leaves damaged.",
        "action": "Iron hook ഉപയോഗിച്ചു beetle നീക്കം ചെയ്ത് Naphthalene balls (4–5) വെക്കുക. Chlorpyrifos (5ml/litre) inject ചെയ്യുക.",
        "prevention": "Dead wood, compost heaps remove ചെയ്യുക — breeding sites ഇല്ലാതാക്കുക.",
    },
    "Pepper": {
        "title": "🔴 Phytophthora (Quick Wilt) — High Alert",
        "severity": "high",
        "symptoms": "ഒരു vine മൊത്തം പെട്ടെന്ന് wilting; roots rotting.",
        "action": "Copper Oxychloride (3g/litre) root-zone drench ആഴ്ചതോറും. Drainage ഉറപ്പ് വരുത്തുക. Infected vines remove ചെയ്ത് burn ചെയ്യുക.",
        "prevention": "Monsoon-നു മുൻപ് Trichoderma (10g/plant) soil-ൽ apply ചെയ്യുക.",
    },
    "Banana": {
        "title": "ℹ️ Panama Wilt (Fusarium oxysporum)",
        "severity": "low",
        "symptoms": "Lower leaves yellowing; pseudostem internal browning.",
        "action": "Infected plants remove ചെയ്ത് burn ചെയ്യുക. Carbendazim (1g/litre) drench ചെയ്യുക.",
        "prevention": "Disease-free tissue culture plants മാത്രം ഉപയോഗിക്കുക.",
    },
    "Ginger": {
        "title": "⚠️ Soft Rot (Pythium aphanidermatum)",
        "severity": "medium",
        "symptoms": "Rhizome soft ആകുന്നു; foul smell; plants collapse.",
        "action": "Metalaxyl+Mancozeb (2.5g/litre) soil drench — 15 ദിവസം ഇടവിട്ട്. Waterlogging ഒഴിവാക്കുക.",
        "prevention": "Treat seed rhizomes with Mancozeb (3g/litre) before planting.",
    },
    "Rubber": {
        "title": "⚠️ Pink Disease (Corticium salmonicolor)",
        "severity": "medium",
        "symptoms": "Branches-ൽ pink/salmon coating; die-back.",
        "action": "Affected bark scrape ചെയ്ത് Copper Oxychloride paste apply ചെയ്യുക.",
        "prevention": "Monsoon-ൽ Bordeaux mixture spray ചെയ്യുക.",
    },
    "Tapioca": {
        "title": "ℹ️ Mosaic Virus (SLCMV)",
        "severity": "low",
        "symptoms": "Leaves mosaic pattern; stunted growth.",
        "action": "Infected plants remove ചെയ്ത് destroy ചെയ്യുക. Aphids control: Imidacloprid (0.3ml/litre).",
        "prevention": "Virus-free planting material ഉപയോഗിക്കുക.",
    },
    "Vegetables": {
        "title": "⚠️ Thrips & Whitefly",
        "severity": "medium",
        "symptoms": "Leaves curling; silvery streaks; sooty mold.",
        "action": "Yellow sticky traps set ചെയ്യുക. Spinosad (0.5ml/litre) spray ചെയ്യുക.",
        "prevention": "Reflective mulch ഉപയോഗിക്കുക.",
    },
}

async def fetch_pest_bulletin(crop: str, district: str) -> dict:
    """SIMULATED Kerala Agriculture Department bulletin."""
    data = PEST_DATA.get(crop, {
        "title": "ℹ️ No Active Pest Alerts",
        "severity": "none",
        "symptoms": "No significant pest activity reported.",
        "action": "Regular field scouting continue ചെയ്യുക.",
        "prevention": "Good agricultural practices maintain ചെയ്യുക.",
    })
    return {
        **data,
        "crop":       crop,
        "district":   district,
        "source":     "Kerala Agriculture Dept (simulated)",
        "fetched_at": datetime.now().isoformat(),
    }
