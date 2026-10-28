import os
import time
from contextlib import asynccontextmanager
from datetime import date
from typing import List

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware

from app import database as db
from app.models import Zone, ZoneAircraft
from app.opensky_client import OpenSkyError, fetch_states

CACHE_SECONDS = 60                                        
DAILY_LIMIT = int(os.getenv("DAILY_CREDIT_LIMIT", "3000"))
cache = {}                                               
usage = {"day": date.today(), "credits": 0}


@asynccontextmanager
async def lifespan(app):
    db.init_db()  
    yield


app = FastAPI(title="Airzone", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["GET"], allow_headers=["*"])


def credit_cost(z):
    """Estimated OpenSky cost by bounding-box area (square degrees)."""
    area = (z["lamax"] - z["lamin"]) * (z["lomax"] - z["lomin"])
    return 1 if area <= 25 else 2 if area <= 100 else 3 if area <= 400 else 4


def credits_today():
    if usage["day"] != date.today():
        usage.update(day=date.today(), credits=0)
    return usage["credits"]


@app.get("/api/health")
def health():
    return {"status": "ok", "credits_used_today": credits_today(), "daily_limit": DAILY_LIMIT}


@app.get("/api/zones", response_model=List[Zone])
def zones():
    return db.list_zones()


@app.get("/api/zones/{zone_id}", response_model=Zone)
def zone(zone_id: str = Path(pattern=r"^[A-Za-z0-9-]{1,30}$")):
    found = db.get_zone(zone_id)
    if not found:
        raise HTTPException(404, "Zone not found.")
    return found


@app.get("/api/zones/{zone_id}/aircraft", response_model=ZoneAircraft)
def zone_aircraft(zone_id: str = Path(pattern=r"^[A-Za-z0-9-]{1,30}$")):
    z = db.get_zone(zone_id)
    if not z:
        raise HTTPException(404, "Zone not found.")

    hit = cache.get(zone_id)
    if hit and time.time() - hit["fetched_at"] < CACHE_SECONDS:
        return {**hit, "cached": True, "credits_used_today": credits_today()}

    cost = credit_cost(z)
    if credits_today() + cost > DAILY_LIMIT:
        raise HTTPException(429, "Local daily credit limit reached. Try again tomorrow or raise DAILY_CREDIT_LIMIT.")
    try:
        result = fetch_states(z["lamin"], z["lomin"], z["lamax"], z["lomax"])
    except OpenSkyError as e:
        raise HTTPException(e.status, e.message)

    usage["credits"] += cost
    now = int(time.time())
    saved = db.save_observations(result["aircraft"], now)
    payload = {"zone": z, "time": result["time"], "count": len(result["aircraft"]),
               "with_position": sum(a["has_position"] for a in result["aircraft"]),
               "aircraft": result["aircraft"], "fetched_at": now, "saved": saved,
               "credits_remaining": result["credits_remaining"]}
    cache[zone_id] = payload
    return {**payload, "cached": False, "credits_used_today": usage["credits"]}


@app.get("/api/aircraft/{icao24}")
def aircraft(icao24: str = Path(pattern=r"^[0-9a-fA-F]{6}$")):
    history = db.aircraft_history(icao24.lower())
    if not history:
        raise HTTPException(404, "No saved observations for this aircraft yet.")
    return {"icao24": icao24.lower(), "latest": history[0], "history": history}
