const DIRS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"];

export function direction(deg) {
  if (deg === null || deg === undefined) return "Not available";
  return DIRS[Math.round(deg / 45) % 8];
}

export function height(a) {
  if (a.on_ground) return "At ground level";
  const m = a.baro_altitude ?? a.geo_altitude;
  if (m === null || m === undefined) return "Not available";
  return m >= 1000 ? `${(m / 1000).toFixed(1)} km high` : `${Math.round(m)} m high`;
}

export function speed(a) {
  return a.velocity_kmh == null ? "Not available" : `${Math.round(a.velocity_kmh)} km/h`;
}

export function climb(rate) {
  if (rate == null) return "Not available";
  if (rate > 1) return "Climbing";
  if (rate < -1) return "Descending";
  return "Level flight";
}

export function ago(ts) {
  if (!ts) return "Not available";
  const s = Math.max(0, Math.round(Date.now() / 1000 - ts));
  if (s < 60) return "Just now";
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  return `${Math.round(s / 3600)} h ago`;
}