"""models.py — Pydantic request/response models"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class Farmer(BaseModel):
    id: Optional[str] = None
    name: str
    district: str
    crop: str
    phone: Optional[str] = ""
    lang: Optional[str] = "Malayalam"
    land: Optional[str] = "1"
    emoji: Optional[str] = "👨‍🌾"

class Message(BaseModel):
    farmer_id: str
    message: str
    type: Optional[str] = "morning_advisory"

class QARequest(BaseModel):
    farmer_id: str
    question: str
    conversation_history: Optional[List[Dict[str, Any]]] = []

class QAResponse(BaseModel):
    answer: str
    farmer_id: str
