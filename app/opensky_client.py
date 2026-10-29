import os
import time
import ssl
 
import httpx
from dotenv import load_dotenv
 
load_dotenv()
 
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
API_URL = "https://opensky-network.org/api/states/all"
 
FIELDS = ["icao24", "callsign", "origin_country", "time_position", "last_contact",
          "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
          "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
          "spi", "position_source"]
 
http = httpx.Client(timeout=15.0, verify=ssl.create_default_context())  # same library as the old working code
 
 
class OpenSkyError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.message, self.status = message, status
 
 
class TokenManager:
    def __init__(self):
        self.token, self.expires_at = None, 0
 
    def get(self, force=False):
        if not force and self.token and time.time() < self.expires_at - 30:
            return self.token
        cid, secret = os.getenv("OPENSKY_CLIENT_ID"), os.getenv("OPENSKY_CLIENT_SECRET")
        if not cid or not secret:
            raise OpenSkyError("OpenSky credentials are missing in .env", 500)
        try:
            r = http.post(TOKEN_URL, data={
                "grant_type": "client_credentials", "client_id": cid, "client_secret": secret})
        except httpx.TimeoutException:
            raise OpenSkyError("OpenSky login timed out.", 504)
        except httpx.HTTPError as e:
            print("Token request failed:", type(e).__name__)  # class name only, no secrets
            raise OpenSkyError("Could not reach the OpenSky login server.", 502)
        if r.status_code != 200:
            raise OpenSkyError("OpenSky authentication failed. Check your credentials.", 502)
        body = r.json()
        self.token = body["access_token"]
        self.expires_at = time.time() + body.get("expires_in", 300)
        return self.token
 
 
tokens = TokenManager()
 
 
def normalize(raw):
    a = {name: (raw[i] if i < len(raw) else None) for i, name in enumerate(FIELDS)}
    a["callsign"] = (a["callsign"] or "").strip() or None
    a["velocity_kmh"] = round(a["velocity"] * 3.6, 1) if a["velocity"] is not None else None
    a["has_position"] = a["latitude"] is not None and a["longitude"] is not None
    return a
 
 
def fetch_states(lamin, lomin, lamax, lomax):
    params = {"lamin": lamin, "lomin": lomin, "lamax": lamax, "lomax": lomax}
    r = None
    for attempt in (0, 1):  # retry once with a fresh token on 401
        try:
            r = http.get(API_URL, params=params,
                         headers={"Authorization": f"Bearer {tokens.get(force=attempt == 1)}"})
        except httpx.TimeoutException:
            raise OpenSkyError("OpenSky request timed out.", 504)
        except httpx.HTTPError as e:
            print("States request failed:", type(e).__name__)
            raise OpenSkyError("Could not reach OpenSky.", 502)
        if r.status_code != 401:
            break
    if r.status_code == 401:
        raise OpenSkyError("OpenSky rejected the access token.", 502)
    if r.status_code == 403:
        raise OpenSkyError("OpenSky denied access (HTTP 403).", 502)
    if r.status_code == 429:
        wait = r.headers.get("X-Rate-Limit-Retry-After-Seconds")
        raise OpenSkyError("OpenSky rate limit reached." + (f" Retry in {wait}s." if wait else ""), 429)
    if r.status_code != 200:
        raise OpenSkyError(f"OpenSky returned an unexpected status ({r.status_code}).", 502)
 
    data = r.json()
    states = data.get("states") or []
    remaining = r.headers.get("X-Rate-Limit-Remaining")
    return {"time": data.get("time"), "aircraft": [normalize(s) for s in states],
            "credits_remaining": int(remaining) if remaining and remaining.isdigit() else None}