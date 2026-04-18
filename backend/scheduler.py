"""
scheduler.py
APScheduler — runs the daily advisory generation at a configurable time.
Default: 6:00 AM. Can be changed via the /api/scheduler/set-time endpoint.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import asyncio

scheduler = AsyncIOScheduler()
_current_hour   = 6
_current_minute = 0

async def run_daily_advisory():
    """Called by scheduler every day at the configured time."""
    print(f"\n{'='*50}")
    print(f"⏰ SCHEDULER TRIGGERED at {datetime.now().strftime('%H:%M:%S')}")
    print(f"📱 Generating advisories for all farmers...")
    print(f"{'='*50}")
    try:
        from database import db
        from data_fetcher import fetch_market_prices, fetch_weather, fetch_pest_bulletin
        from message_composer import compose_advisory_message

        farmers = await db.get_all_farmers()
        print(f"Found {len(farmers)} farmers to notify")

        for farmer in farmers:
            try:
                prices  = await fetch_market_prices(farmer["crop"], farmer["district"])
                weather = await fetch_weather(farmer["district"])
                pest    = await fetch_pest_bulletin(farmer["crop"], farmer["district"])
                message = await compose_advisory_message(farmer, prices, weather, pest)

                msg_record = {
                    "farmer_id":   farmer["id"],
                    "farmer_name": farmer["name"],
                    "crop":        farmer["crop"],
                    "district":    farmer["district"],
                    "message":     message,
                    "prices":      prices,
                    "weather":     weather,
                    "pest":        pest,
                    "type":        "morning_advisory",
                }
                await db.save_message(msg_record)
                print(f"  ✅ Advisory generated for {farmer['name']}")
            except Exception as e:
                print(f"  ❌ Error for {farmer['name']}: {e}")

        print(f"✅ All advisories generated at {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"❌ Scheduler error: {e}")


def start_scheduler():
    global _current_hour, _current_minute
    scheduler.add_job(
        run_daily_advisory,
        CronTrigger(hour=_current_hour, minute=_current_minute),
        id="daily_advisory",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    print(f"⏰ Scheduler started — Daily advisory at {_current_hour:02d}:{_current_minute:02d}")


def update_schedule_time(hour: int, minute: int = 0):
    global _current_hour, _current_minute
    _current_hour   = hour
    _current_minute = minute
    scheduler.reschedule_job(
        "daily_advisory",
        trigger=CronTrigger(hour=hour, minute=minute),
    )
    print(f"⏰ Schedule updated to {hour:02d}:{minute:02d}")


def get_scheduler_status():
    job = scheduler.get_job("daily_advisory")
    return {
        "running":      scheduler.running,
        "scheduled_time": f"{_current_hour:02d}:{_current_minute:02d}",
        "next_run":     str(job.next_run_time) if job else "N/A",
        "hour":         _current_hour,
        "minute":       _current_minute,
    }
