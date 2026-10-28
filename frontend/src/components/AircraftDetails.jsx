import { useEffect, useState } from "react";
import { getAircraftHistory, num, text, when } from "../api";
import { ago, climb, direction, height, speed } from "../plain";

const SOURCES = ["ADS-B", "ASTERIX", "MLAT", "FLARM"];

export default function AircraftDetails({ aircraft: a, onClose }) {
  const [seen, setSeen] = useState(0);

  useEffect(() => {
    setSeen(0);
    getAircraftHistory(a.icao24).then((h) => setSeen(h.history.length)).catch(() => setSeen(0));
  }, [a.icao24]);

  const technical = [
    ["ICAO24 code", a.icao24],
    ["Coordinates", a.has_position ? `${a.latitude}, ${a.longitude}` : "Not available"],
    ["Position time", when(a.time_position)],
    ["Last contact", when(a.last_contact)],
    ["Barometric altitude", num(a.baro_altitude, " m")],
    ["Geometric altitude", num(a.geo_altitude, " m")],
    ["Speed", a.velocity === null ? "Not available" : `${num(a.velocity, " m/s", 1)}`],
    ["Heading", num(a.true_track, "°")],
    ["Vertical rate", num(a.vertical_rate, " m/s", 1)],
    ["Squawk", text(a.squawk)],
    ["Position source", SOURCES[a.position_source] ?? text(a.position_source)],
    ["Category", "Not requested from OpenSky"],
  ];

  return (
    <div className="detail-card">
      <button className="close" onClick={onClose} aria-label="Close">×</button>
      <h2>{a.callsign || "Unknown flight"}</h2>
      <p className="muted">Registered in {text(a.origin_country)}</p>
      <span className={"badge " + (a.on_ground ? "ground" : "air")}>
        {a.on_ground ? "On the ground" : "In the air"}
      </span>

      <div className="tiles">
        <div><small>Height</small><b>{height(a)}</b></div>
        <div><small>Speed</small><b>{speed(a)}</b></div>
        <div><small>Heading</small><b>{direction(a.true_track)}</b></div>
        <div><small>Movement</small><b>{climb(a.vertical_rate)}</b></div>
        <div><small>Last heard</small><b>{ago(a.last_contact)}</b></div>
        <div><small>Route</small><b>Not available</b></div>
      </div>

      <p className="muted">
        The country shows where the aircraft is registered, not where it took off.
        Departure and destination can't be found from this data.
      </p>
      {seen > 0 && <p className="muted">This app has recorded this aircraft {seen} time{seen > 1 ? "s" : ""}.</p>}

      <details>
        <summary>Technical details</summary>
        <dl>{technical.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
      </details>
    </div>
  );
}