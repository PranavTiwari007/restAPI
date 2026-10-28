import AircraftCard from "./AircraftCard";

export default function AircraftList({ zone, data, loading, error, selectedIcao, onSelect }) {
  let body;
  if (!zone) body = <p className="muted">No zone selected yet.</p>;
  else if (loading) body = <p className="state">Loading aircraft…</p>;
  else if (error) body = <p className="state error">{error}</p>;
  else if (data && data.count === 0)
    body = <p className="muted">No aircraft in this snapshot. This does not mean the sky is empty; OpenSky only reports what its receivers have seen.</p>;
  else if (data)
    body = (
      <>
        <p className="muted">
          {data.count} returned by OpenSky, {data.with_position} with a usable position.
          This is the latest available snapshot, not a complete live feed.
        </p>
        {data.aircraft.filter((a) => a.has_position).map((a) => (
          <AircraftCard key={a.icao24} aircraft={a} active={a.icao24 === selectedIcao} onSelect={onSelect} />
        ))}
      </>
    );
  return (
    <section id="aircraft" className="panel">
      <h2>Aircraft{data && !loading ? ` (${data.count})` : ""}</h2>
      {body}
    </section>
  );
}
