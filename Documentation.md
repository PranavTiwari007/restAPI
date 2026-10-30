# Airzone project documentation

## Overview

Airzone is a React and FastAPI application for collecting OpenSky aircraft-state snapshots around selected airports and reviewing observations through a map and REST API.

OpenSky state vectors describe aircraft observations at a point in time. They do not provide airline schedules, routes, or verified takeoff and landing events. Airzone's daily metric counts distinct aircraft observed in stored samples; it is not a flight-movement or total-traffic count.

## Workflow

1. The frontend searches the backend's manually curated airport catalog.
2. The selected airport determines an approximate 22 km by 22 km square centered on its reference coordinates.
3. The user manually requests a new snapshot through a POST endpoint.
4. The backend fetches state vectors from OpenSky and stores the import and positioned aircraft observations in SQLite.
5. The frontend reads the latest saved snapshot, displays aircraft positions, and lets the user search callsigns or ICAO24 identifiers.
6. A daily endpoint groups saved samples by UTC date and counts distinct ICAO24 aircraft. Dates with no samples are returned as missing data, not as zero.

The catalog includes the Indian airports classified as International or International (CE) in the [List of airports in India](https://en.wikipedia.org/wiki/List_of_airports_in_India), based on the Airports Authority of India's March 2026 traffic statistics, plus a selected set of airports worldwide. Coordinates are from the [OurAirports public-domain data](https://ourairports.com/data/). These are reference coordinates, not operational data; verify current designation and location with the relevant authorities before relying on them.

The map draws the selected approximate 22 km by 22 km square around the airport's catalog coordinate and displays the airport marker at its center. Data collection is manual; the project does not run an automatic polling schedule.

## Technologies

- Python and FastAPI for REST endpoints
- React and Vite for the browser dashboard
- OpenSky Network API for aircraft state vectors
- HTTPX for upstream HTTPS requests
- SQLite for saved samples and history
- Pydantic for response validation
- Leaflet for the map

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Service and local credit-limit status |
| `GET` | `/api/airports?q=...` | Search airport name, city, country, or IATA code |
| `POST` | `/api/airports/{airport_id}/imports` | Manually fetch and save a new snapshot |
| `GET` | `/api/airports/{airport_id}/aircraft` | Read the latest saved snapshot |
| `GET` | `/api/airports/{airport_id}/daily-observations?days=7` | Read distinct aircraft observed and sample counts by UTC day |
| `GET` | `/api/airports/{airport_id}/aircraft/{icao24}/history` | Read one aircraft's saved history for the selected airport |

The original `/api/zones` map-grid routes remain available as a legacy demo. The frontend's airport analysis workflow uses the airport endpoints.

## Run locally

Configure `OPENSKY_CLIENT_ID` and `OPENSKY_CLIENT_SECRET` in `.env`, then run the backend from the repository root:

```powershell
python -m uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open Vite's printed local URL. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Data limits and future scope

- Airzone uses OpenSky's `/states/all` state-vector endpoint. Coverage depends on aircraft transmissions and receiver availability; missing aircraft or positions do not prove an area is empty.
- State vectors are point-in-time observations, not airline schedules or verified takeoff/landing events. They do not establish routes, destinations, or whether an aircraft observed near an airport is using that airport.
- Callsigns, positions, altitude, speed, and other fields may be null or stale. OpenSky may omit a position without a recent position update and can omit obsolete state vectors when updates stop.
- Routes, ADS-C, and MLAT data are not available through the OpenSky REST API used by this project.
- OpenSky rate and credit limits apply. Current documentation lists 4,000 daily credits for standard authenticated access per endpoint family, with actual quotas depending on account tier. `/states/all` costs 1–4 credits according to bounding-box area. Check current provider documentation and the `X-Rate-Limit-Remaining` response header; exhausted quotas can return HTTP 429.
- Airzone fetches only on a user-triggered request; there is no automatic polling. Daily distinct-aircraft metrics count only positioned aircraft in saved samples for that UTC day. Unsampled days are missing data, not zero traffic, and the metric is not a flight-movement count.
- Airzone's local guard currently limits requests to 3,000 estimated credits per day. Its counter is in process memory, resets on restart, and is not shared across multiple backend processes. OpenSky's own quota is authoritative.
- The airport catalog is not global. Its approximate 22 km square uses reference coordinates, which may change and are unsuitable for navigation or operational decisions.
- OpenSky data and Airzone summaries must not be used for operational air-traffic control, navigation, or safety decisions.

See the [OpenSky REST API limitations and credit documentation](https://openskynetwork.github.io/opensky-api/rest.html#limitations) and [OpenSky state-vector notes](https://openskynetwork.github.io/opensky-api/).

- Automatic polling, runway-capacity analysis, and AI analysis are not implemented.
