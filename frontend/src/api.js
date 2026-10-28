const BASE = "http://127.0.0.1:8000/api";

async function get(path) {
  let res;
  try {
    res = await fetch(BASE + path);
  } catch {
    throw new Error("Cannot reach the backend. Is it running on port 8000?");
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `Request failed (${res.status})`);
  return body;
}

export const getZones = () => get("/zones");
export const getZoneAircraft = (zoneId) => get(`/zones/${zoneId}/aircraft`);
export const getAircraftHistory = (icao24) => get(`/aircraft/${icao24}`);

export const num = (v, unit = "", digits = 0) =>
  v === null || v === undefined ? "Not available" : `${Number(v).toFixed(digits)}${unit}`;
export const text = (v) => (v === null || v === undefined || v === "" ? "Not available" : String(v));
export const when = (ts) => (ts ? new Date(ts * 1000).toLocaleString() : "Not available");
