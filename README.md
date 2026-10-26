# Aircraft State API

A learning project that will fetch selected live aircraft state data from the OpenSky Network, save snapshots in SQLite, and expose the saved data through a Python REST API.

OpenSky provides ADS-B-derived aircraft tracking information. It does not provide airline schedules or delays. See [plan.md](plan.md) for the planned scope and data fields.

## Current status

The API can manually import bounded OpenSky state vectors, save each import as a SQLite snapshot, and return saved observations. State mapping, OAuth request behavior, and API/database behavior have automated tests; the upstream HTTP calls are mocked in tests.

## Requirements

- Python 3.11 or newer
- An OpenSky API client (needed for live upstream imports)

SQLite is included with Python, so there is no separate database server to install.

## Set up on Windows PowerShell

Create a virtual environment and activate it:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install application dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Configure OpenSky credentials

Create an API client from the [OpenSky account page](https://opensky-network.org/my-opensky/account). Copy the local example file and enter your credentials:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set `OPENSKY_CLIENT_ID` and `OPENSKY_CLIENT_SECRET`. Keep the values private; `.env` and the SQLite database file are ignored by Git.

## Run the API

```powershell
python -m uvicorn app.main:app --reload
```

Then open:

- `http://127.0.0.1:8000/health` — basic service health
- `http://127.0.0.1:8000/docs` — interactive API documentation

## API routes

- `POST /api/v1/state-imports` — send a geographic bounding box (`lamin`, `lomin`, `lamax`, `lomax`) to fetch and save one OpenSky snapshot.
- `GET /api/v1/aircraft-states` — read aircraft observations from the latest snapshot only.
- `GET /api/v1/aircraft-states/{state_id}` — read one saved observation by its database ID, including observations from older snapshots.

To try an import in `/docs`, expand `POST /api/v1/state-imports`, choose **Try it out**, and use this MAA-area example:

```json
{
  "lamin": 12.790005,
  "lomin": 79.969296,
  "lamax": 13.190005,
  "lomax": 80.369296
}
```

Every submission makes a real OAuth request and a real OpenSky state-vector request. Imports are manual; avoid repeatedly submitting the example because the provider applies request limits.

An import is all-or-nothing: if a returned state vector is malformed, the API reports an upstream error and does not save a partial snapshot. Older successful snapshots remain in SQLite.
OpenSky may return no state vectors for a small area at a particular moment. That is recorded as a valid snapshot with `state_count: 0` and an empty `data` list.

## Database and tests

The local database defaults to `data/aircraft.db`. It is created when the API starts; Python's built-in `sqlite3` module means no database server is needed. To inspect it, use a SQLite command-line tool or a SQLite-compatible viewer.

Install test dependencies and run the test suite:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Troubleshooting imports

- `503 OpenSky client credentials are not configured`: confirm `.env` is in the project root and contains non-empty `OPENSKY_CLIENT_ID` and `OPENSKY_CLIENT_SECRET` entries. Never print or share their values.
- `502 Unable to contact the OpenSky service`: check network access to OpenSky and the local server log for the safe failure type. The API does not save a snapshot when the upstream request fails.
- An OpenSky HTTP error is returned as a `502` with its HTTP status code; check the current OpenSky authentication requirements, request limits, and account status.
- Outbound HTTPS uses Python's system certificate trust store with certificate verification enabled. Do not disable TLS verification to work around certificate or network errors.
