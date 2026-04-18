"""
Kerala Farmer Advisory Agent — FastAPI Backend
Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import os
from pathlib import Path

from database import db
from scheduler import start_scheduler
from data_fetcher import fetch_market_prices, fetch_weather, fetch_pest_bulletin
from message_composer import compose_advisory_message
from models import Farmer, Message, QARequest, QAResponse

app = FastAPI(title="Kerala Farmer Advisory Agent", version="1.0.0")

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(str(frontend_path / "index.html"))

# ─── STARTUP ───────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await db.init()
    await db.seed_demo_farmers()
    start_scheduler()
    print("✅ Kerala Farmer Advisory Agent started!")

# ─── FARMER ENDPOINTS ──────────────────────────────────────
@app.get("/api/farmers")
async def get_farmers():
    return await db.get_all_farmers()

@app.post("/api/farmers")
async def create_farmer(farmer: Farmer):
    result = await db.add_farmer(farmer.dict())
    return result

@app.delete("/api/farmers/{farmer_id}")
async def delete_farmer(farmer_id: str):
    await db.delete_farmer(farmer_id)
    return {"status": "deleted"}

# ─── ADVISORY ENDPOINTS ────────────────────────────────────
@app.post("/api/advisory/generate/{farmer_id}")
async def generate_advisory(farmer_id: str):
    """Generate and store morning advisory for a specific farmer"""
    farmer = await db.get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    prices  = await fetch_market_prices(farmer["crop"], farmer["district"])
    weather = await fetch_weather(farmer["district"])
    pest    = await fetch_pest_bulletin(farmer["crop"], farmer["district"])

    message = await compose_advisory_message(farmer, prices, weather, pest)

    msg_record = {
        "farmer_id": farmer_id,
        "farmer_name": farmer["name"],
        "crop": farmer["crop"],
        "district": farmer["district"],
        "message": message,
        "prices": prices,
        "weather": weather,
        "pest": pest,
        "type": "morning_advisory"
    }
    saved = await db.save_message(msg_record)
    return saved

@app.post("/api/advisory/generate-all")
async def generate_all_advisories():
    """Trigger advisory generation for all farmers (simulates 6AM scheduler)"""
    farmers = await db.get_all_farmers()
    results = []
    for farmer in farmers:
        try:
            prices  = await fetch_market_prices(farmer["crop"], farmer["district"])
            weather = await fetch_weather(farmer["district"])
            pest    = await fetch_pest_bulletin(farmer["crop"], farmer["district"])
            message = await compose_advisory_message(farmer, prices, weather, pest)
            msg_record = {
                "farmer_id": farmer["id"],
                "farmer_name": farmer["name"],
                "crop": farmer["crop"],
                "district": farmer["district"],
                "message": message,
                "prices": prices,
                "weather": weather,
                "pest": pest,
                "type": "morning_advisory"
            }
            saved = await db.save_message(msg_record)
            results.append(saved)
        except Exception as e:
            results.append({"farmer_id": farmer["id"], "error": str(e)})
    return {"status": "done", "count": len(results), "messages": results}

@app.get("/api/messages")
async def get_messages():
    return await db.get_all_messages()

@app.get("/api/messages/{farmer_id}")
async def get_farmer_messages(farmer_id: str):
    return await db.get_farmer_messages(farmer_id)

@app.delete("/api/messages")
async def clear_messages():
    await db.clear_messages()
    return {"status": "cleared"}

# ─── Q&A ENDPOINT ──────────────────────────────────────────
@app.post("/api/qa")
async def qa_handler(req: QARequest):
    """Handle reactive Q&A from farmers"""
    farmer = await db.get_farmer(req.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    from qa_handler import answer_farmer_question
    answer = await answer_farmer_question(farmer, req.question, req.conversation_history)

    qa_record = {
        "farmer_id": req.farmer_id,
        "farmer_name": farmer["name"],
        "crop": farmer["crop"],
        "district": farmer["district"],
        "message": f"Q: {req.question}\nA: {answer}",
        "type": "qa",
        "question": req.question,
        "answer": answer
    }
    await db.save_message(qa_record)
    return {"answer": answer}

# ─── EVALUATION ENDPOINT ───────────────────────────────────
@app.get("/api/evaluation/dataset")
async def get_eval_dataset():
    from evaluation import get_evaluation_dataset
    return get_evaluation_dataset()

@app.post("/api/evaluation/run")
async def run_evaluation():
    from evaluation import run_full_evaluation
    return await run_full_evaluation()

# ─── DATA ENDPOINTS ────────────────────────────────────────
@app.get("/api/data/prices/{crop}/{district}")
async def get_prices(crop: str, district: str):
    return await fetch_market_prices(crop, district)

@app.get("/api/data/weather/{district}")
async def get_weather(district: str):
    return await fetch_weather(district)

@app.get("/api/data/pest/{crop}/{district}")
async def get_pest(crop: str, district: str):
    return await fetch_pest_bulletin(crop, district)

# ─── SCHEDULER CONTROL ─────────────────────────────────────
@app.get("/api/scheduler/status")
async def scheduler_status():
    from scheduler import get_scheduler_status
    return get_scheduler_status()

@app.post("/api/scheduler/set-time")
async def set_schedule_time(hour: int, minute: int = 0):
    """Change the daily advisory time (e.g., hour=10, minute=0 for 10AM)"""
    from scheduler import update_schedule_time
    update_schedule_time(hour, minute)
    return {"status": "updated", "time": f"{hour:02d}:{minute:02d}"}
