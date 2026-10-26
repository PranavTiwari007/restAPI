# Flight Data REST API — Project Plan

## Problem and proposed approach

Turn the meeting notes into a beginner-friendly Python project that consumes a free external flight-data API, stores selected results in MySQL, and exposes those stored results through its own REST API. The starter folder is empty, and the project will use MySQL Workbench as the desktop client for inspecting a locally running MySQL server.

Use Aviationstack's free personal plan for an educational, non-commercial project. Its published plan currently advertises real-time flight data and 100 requests per month; it requires an API key. Keep upstream calls explicit and bounded: a manual `POST /api/v1/flight-imports` action fetches and saves results, while `GET /api/v1/flights` and `GET /api/v1/flights/{id}` read from MySQL. This avoids spending a provider request for every read and makes the data lifecycle easy to understand.

## Proposed project flow

```mermaid
flowchart LR
    U[User / Swagger UI] -->|POST import| A[Python FastAPI app]
    A -->|GET flight data + API key| X[Aviationstack]
    X -->|JSON response| A
    A -->|validate and map| D[(MySQL database)]
    U -->|GET saved flights| A
    A -->|SELECT| D
    D -->|saved records| A
    A -->|JSON response| U
    W[MySQL Workbench] -. inspect and query .-> D
    G[GitHub] -. source, schema and docs .-> A
```

## Concepts and boundaries

- **REST:** the app's HTTP interface; explain resources, URLs, methods, status codes, JSON, query parameters, and stateless requests using the project routes.
- **Two APIs:** Aviationstack is the upstream API the app consumes; the FastAPI service is the REST API the project builds for its users.
- **MySQL and Workbench:** MySQL Server stores rows and executes queries. Workbench is a GUI client used to connect to that server and inspect tables; it is not the server or the application's storage location.
- **Git and GitHub:** Git records project changes locally; GitHub hosts the code and documentation remotely. The repo may include setup instructions, SQL schema, and `.env.example`, but must exclude API keys, real `.env` files, and database contents.
- Keep the first version API-only; FastAPI's generated Swagger UI provides an interactive way to try endpoints, without a separate frontend.
- Model each import as stored flight data with an import timestamp, so a later import can preserve a new observation rather than silently erasing the prior one. Select fields from the provider response only after checking its current API documentation.
- Provider limits and data availability can change. Keep the import request limited to a small, documented sample, handle upstream errors explicitly, and avoid automated polling.

## Implementation todos

1. Confirm current Aviationstack endpoint, query filters, response shape, free-plan limits, and key handling; document the exact chosen sample request.
2. Define the app structure, MySQL schema, REST routes, data mapping, environment configuration, and error behavior.
3. Build the FastAPI service and database integration, including explicit import and stored-data retrieval endpoints.
4. Add focused tests for mapping, routes, validation, and upstream/database error paths using mocked external calls where appropriate.
5. Write step-by-step documentation: REST/API concepts, prerequisites and MySQL Workbench connection, API-key setup, configuration, schema/import flow, endpoint examples, flowchart, Git/GitHub workflow, and troubleshooting.
6. Initialize a local Git repository, add safe ignore/config examples, validate the setup and tests, and explain how to create/connect the GitHub remote and push the project.

## Research references

- [Aviationstack pricing](https://aviationstack.com/pricing) — free plan, request quota, non-commercial use, and listed flight-data capabilities.
- [Aviationstack API documentation](https://docs.apilayer.com/aviationstack/docs/api-documentation) — endpoint and response details to confirm before implementation.
- [OpenSky REST API](https://openskynetwork.github.io/opensky-api/rest.html) — considered alternative for aircraft state/position data, which is different from flight schedule/status data.
