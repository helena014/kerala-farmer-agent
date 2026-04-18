"""
database.py — SQLite database layer
Uses SQLite so you don't need to install PostgreSQL.
(In production, swap the DATABASE_URL for PostgreSQL.)
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "farmer_agent.db"

DEMO_FARMERS = [
    {"id": "f1", "name": "Rajan P.K.",   "district": "Palakkad", "crop": "Rice",    "phone": "+91 9447123456", "lang": "Malayalam", "land": "3.5", "emoji": "👨‍🌾"},
    {"id": "f2", "name": "Mariamma K.",  "district": "Thrissur", "crop": "Coconut", "phone": "+91 9387654321", "lang": "Malayalam", "land": "2.0", "emoji": "👩‍🌾"},
    {"id": "f3", "name": "Suresh Nair",  "district": "Wayanad",  "crop": "Pepper",  "phone": "+91 9446789012", "lang": "Malayalam", "land": "1.8", "emoji": "👨‍🌾"},
    {"id": "f4", "name": "Leela Devi",   "district": "Ernakulam","crop": "Banana",  "phone": "+91 9495432109", "lang": "Malayalam", "land": "1.2", "emoji": "👩‍🌾"},
    {"id": "f5", "name": "Gopalan C.R.", "district": "Kozhikode","crop": "Ginger",  "phone": "+91 9447567890", "lang": "Malayalam", "land": "0.8", "emoji": "👨‍🌾"},
]

class Database:
    def __init__(self):
        self.db_path = str(DB_PATH)

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def init(self):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS farmers (
                id       TEXT PRIMARY KEY,
                name     TEXT NOT NULL,
                district TEXT NOT NULL,
                crop     TEXT NOT NULL,
                phone    TEXT,
                lang     TEXT DEFAULT 'Malayalam',
                land     TEXT DEFAULT '1',
                emoji    TEXT DEFAULT '👨‍🌾',
                created_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id          TEXT PRIMARY KEY,
                farmer_id   TEXT,
                farmer_name TEXT,
                crop        TEXT,
                district    TEXT,
                message     TEXT,
                prices      TEXT,
                weather     TEXT,
                pest        TEXT,
                type        TEXT DEFAULT 'morning_advisory',
                question    TEXT,
                answer      TEXT,
                created_at  TEXT
            )
        """)
        conn.commit()
        conn.close()
        print("✅ Database initialised")

    async def seed_demo_farmers(self):
        conn = self._get_conn()
        c = conn.cursor()
        for f in DEMO_FARMERS:
            c.execute("SELECT id FROM farmers WHERE id=?", (f["id"],))
            if not c.fetchone():
                c.execute("""
                    INSERT INTO farmers (id,name,district,crop,phone,lang,land,emoji,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (f["id"], f["name"], f["district"], f["crop"],
                      f["phone"], f["lang"], f["land"], f["emoji"],
                      datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print("✅ Demo farmers seeded")

    async def get_all_farmers(self):
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM farmers ORDER BY created_at").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    async def get_farmer(self, farmer_id: str):
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM farmers WHERE id=?", (farmer_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    async def add_farmer(self, data: dict):
        if not data.get("id"):
         data["id"] = "f" + str(uuid.uuid4())[:8]
        data.setdefault("created_at", datetime.now().isoformat())
        data.setdefault("emoji", "👨‍🌾")
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO farmers (id,name,district,crop,phone,lang,land,emoji,created_at)
            VALUES (:id,:name,:district,:crop,:phone,:lang,:land,:emoji,:created_at)
        """, data)
        conn.commit()
        conn.close()
        return data

    async def delete_farmer(self, farmer_id: str):
        conn = self._get_conn()
        conn.execute("DELETE FROM farmers WHERE id=?", (farmer_id,))
        conn.commit()
        conn.close()

    async def save_message(self, msg: dict):
        msg["id"] = "m" + str(uuid.uuid4())[:8]
        msg["created_at"] = datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO messages
            (id,farmer_id,farmer_name,crop,district,message,prices,weather,pest,type,question,answer,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            msg["id"], msg.get("farmer_id"), msg.get("farmer_name"),
            msg.get("crop"), msg.get("district"), msg.get("message"),
            json.dumps(msg.get("prices", {})),
            json.dumps(msg.get("weather", {})),
            json.dumps(msg.get("pest", {})),
            msg.get("type", "morning_advisory"),
            msg.get("question"), msg.get("answer"),
            msg["created_at"]
        ))
        conn.commit()
        conn.close()
        return msg

    async def get_all_messages(self):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM messages ORDER BY created_at DESC LIMIT 200"
        ).fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            try: d["prices"]  = json.loads(d["prices"] or "{}")
            except: pass
            try: d["weather"] = json.loads(d["weather"] or "{}")
            except: pass
            result.append(d)
        return result

    async def get_farmer_messages(self, farmer_id: str):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM messages WHERE farmer_id=? ORDER BY created_at DESC",
            (farmer_id,)
        ).fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            try: d["prices"]  = json.loads(d["prices"] or "{}")
            except: pass
            try: d["weather"] = json.loads(d["weather"] or "{}")
            except: pass
            result.append(d)
        return result

    async def clear_messages(self):
        conn = self._get_conn()
        conn.execute("DELETE FROM messages")
        conn.commit()
        conn.close()

db = Database()
