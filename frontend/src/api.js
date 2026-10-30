const BASE = "http://127.0.0.1:8000/api";

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(BASE + path, options);
  } catch {
    throw new Error("Cannot reach the backend. Is it running on port 8000?");
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = body.detail;
    throw new Error(
      typeof detail === "string" ? detail : `Request failed (${res.status})`,
    );
  }
  return body;
}

export const getAirports = () => request("/airports");
export const getAirportLatest = (airportId) =>
  request(`/airports/${encodeURIComponent(airportId)}/aircraft`);
export const getDailyObservations = (airportId, days = 7) =>
  request(
    `/airports/${encodeURIComponent(airportId)}/daily-observations?days=${days}`,
  );
export const importAirport = (airportId) =>
  request(`/airports/${encodeURIComponent(airportId)}/imports`, {
    method: "POST",
  });
export const getAirportAircraftHistory = (airportId, icao24) =>
  request(
    `/airports/${encodeURIComponent(airportId)}/aircraft/${encodeURIComponent(icao24)}/history`,
  );

export const num = (v, unit = "", digits = 0) =>
  v === null || v === undefined ? "Not available" : `${Number(v).toFixed(digits)}${unit}`;
export const text = (v) => (v === null || v === undefined || v === "" ? "Not available" : String(v));
export const when = (ts) => (ts ? new Date(ts * 1000).toLocaleString() : "Not available");
