# Airzone

Airzone is a React dashboard and FastAPI service for manually collecting and reviewing OpenSky aircraft-state observations around selected airports. It displays the latest saved snapshot, supports callsign/ICAO24 search, and summarizes distinct aircraft observed per UTC day from saved samples.

OpenSky state vectors are point-in-time observations. They are not airline schedules or verified takeoff/landing records. Daily metrics in this application are **distinct aircraft observed**, not flight movements or a complete count of traffic.

## Requirements

- Python 3.11 or newer
- Node.js and npm
- OpenSky Network API client credentials for fetching new snapshots

The backend uses SQLite; no separate database server is needed.

## Configure OpenSky credentials

Create an API client from the [OpenSky account page](https://opensky-network.org/my-opensky/account). Copy the local example and set `OPENSKY_CLIENT_ID` and `OPENSKY_CLIENT_SECRET` in `.env`:

```powershell
Copy-Item .env.example .env
```

Keep the credentials private. They are used by the backend and are never sent to the browser.

## Run the applications on Windows PowerShell

In the project root, create and activate a virtual environment and install backend dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the backend in one terminal:

```powershell
python -m uvicorn app.main:app --reload
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open the frontend URL printed by Vite (normally `http://localhost:5173`). The API documentation is at `http://127.0.0.1:8000/docs`.

## Airport analysis workflow

1. Search for an airport by name, city, country, or IATA code.
2. Select the airport to view its saved snapshot and daily observation summary.
3. Choose **Fetch latest snapshot** to make a manual POST request to OpenSky.
4. Review the aircraft with usable positions on the map or search the list by callsign or ICAO24.

The catalog in `app/airports.py` includes India's designated international airports (including civil enclaves) and a selected set of airports worldwide; it is not a global airport directory. Airport classifications follow the [List of airports in India](https://en.wikipedia.org/wiki/List_of_airports_in_India), which cites the Airports Authority of India's March 2026 traffic statistics. Reference coordinates are from the [OurAirports public-domain data](https://ourairports.com/data/). Both classifications and coordinates can change; confirm them with the relevant authorities before relying on them.

The map displays the airport reference point and the approximate 22 km by 22 km square centered on that point. Coordinates and area are for analysis only, not for navigation or operational decisions.

Daily values count distinct ICAO24 aircraft with positions in stored airport-area samples for that UTC day. Sampling is manual; select **Fetch latest snapshot** to add a sample. A day with no samples is unknown and shown as missing data, not zero traffic. Repeated samples help build the daily observed-aircraft set; this metric is not a verified count of flight movements. No automatic polling or runway-capacity analysis is included.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Service and local credit-limit status |
| `GET` | `/api/airports?q=chennai` | Search the curated airport catalog |
| `POST` | `/api/airports/MAA/imports` | Manually fetch and persist an airport-area snapshot |
| `GET` | `/api/airports/MAA/aircraft` | Read the latest saved airport snapshot |
| `GET` | `/api/airports/MAA/daily-observations?days=7` | Read daily distinct-aircraft counts and sample coverage (1–90 days) |
| `GET` | `/api/airports/MAA/aircraft/abc123/history` | Read saved history for an aircraft at one airport |

The older `/api/zones` endpoints remain available for the original map-grid demo. The airport dashboard uses the airport endpoints above.

OpenSky access is subject to provider availability and request limits. The backend applies a local daily credit limit and reports provider errors; avoid repeatedly fetching the same area.

## Data and API limitations

Airzone uses OpenSky's `/states/all` state-vector endpoint. Treat its results as observations, not as a complete picture of airport operations:

- **Coverage is incomplete.** Data depends on aircraft transmissions and receiver coverage, which varies by location and time. A missing aircraft or position does not mean the airspace is empty.
- **Not schedules or verified movements.** State vectors do not provide airline schedules, routes, destinations, or delays. Seeing an aircraft in an airport-area box does not establish that it is arriving at or departing from that airport, and the API does not provide verified takeoff/landing counts.
- **Values can be missing or stale.** Callsigns, positions, altitude, speed, and other fields may be null. OpenSky may omit a position when it has not received a recent position update; state vectors can become obsolete and disappear when updates stop.
- **No routes, ADS-C, or MLAT in this REST API.** OpenSky documents those data types as unavailable through its REST API.
- **Provider quotas apply.** The current OpenSky documentation lists 4,000 daily credits for standard authenticated access to each endpoint family; the actual allowance depends on the account tier and may change. `/states/all` uses 1–4 credits depending on bounding-box area. Exhausted quotas can return HTTP 429; check the provider's current documentation and `X-Rate-Limit-Remaining` response header.
- **Manual sampling limits daily summaries.** Airzone only fetches when a user requests a snapshot; it does not continuously poll. Daily distinct-aircraft totals include only aircraft with positions in samples saved that UTC day. Unsampled days are unknown, not zero, and this metric is not a flight-movement count.
- **Local credit guard is approximate and process-local.** Airzone currently caps requests at 3,000 estimated credits per day. The counter resets when the backend restarts and is not shared across multiple backend processes. OpenSky's own quota remains authoritative.
- **Airport area and catalog are approximate.** The 22 km square is centered on reference coordinates and is intended for analysis, not navigation or operational decisions. The catalog is not a complete global airport directory, and airport classifications/coordinates may change.

Do not use these observations or derived summaries for operational air-traffic control, navigation, or safety decisions. See the [OpenSky REST API limitations and credit documentation](https://openskynetwork.github.io/opensky-api/rest.html#limitations) and [OpenSky state-vector notes](https://openskynetwork.github.io/opensky-api/).

## Database and tests

The local database defaults to `data/airzone.db` and is initialized when the API starts. Run tests with:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Build the frontend with:

```powershell
cd frontend
npm ci
npm run build
```
