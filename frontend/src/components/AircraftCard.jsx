import { ago, direction, height, speed } from "../plain";

export default function AircraftCard({ aircraft: a, active, onSelect }) {
  return (
    <div className={"card" + (active ? " active" : "")} onClick={() => onSelect(a)}>
      <div className="row">
        <b className="flight">{a.callsign || "Unknown flight"}</b>
        <span className={"badge " + (a.on_ground ? "ground" : "air")}>
          {a.on_ground ? "On the ground" : "In the air"}
        </span>
      </div>
      <div className="muted">{a.origin_country || "Country not available"} · heard {ago(a.last_contact)}</div>
      <div className="facts">
        <span>{height(a)}</span>
        <span>{speed(a)}</span>
        <span>Heading {direction(a.true_track)}</span>
      </div>
    </div>
  );
}