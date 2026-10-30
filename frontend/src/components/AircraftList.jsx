import { useMemo, useState } from "react";
import AircraftCard from "./AircraftCard";

export default function AircraftList({ airport, data, loading, error, selectedIcao, onSelect }) {
  const [query, setQuery] = useState("");
  const aircraft = data?.data ?? [];
  const filtered = useMemo(() => {
    const term = query.trim().toLocaleLowerCase();
    if (!term) return aircraft;
    return aircraft.filter((record) =>
      [record.callsign, record.icao24]
        .filter(Boolean)
        .some((value) => value.toLocaleLowerCase().includes(term)),
    );
  }, [aircraft, query]);

  let body;
  if (!airport) body = <p className="muted">Choose an airport to see its latest snapshot.</p>;
  else if (loading) body = <p className="state">Loading aircraft…</p>;
  else if (error) body = <p className="state error">{error}</p>;
  else if (data?.snapshot && aircraft.length === 0)
    body = <p className="muted">No aircraft with a position were returned in this snapshot. This does not prove the area is empty; receiver coverage and collection timing affect observations.</p>;
  else if (data?.snapshot)
    body = (
      <>
        <p className="muted">
          Search the latest saved snapshot by callsign or ICAO24. Observations are
          not a continuous live feed or a list of scheduled flights.
        </p>
        <label htmlFor="aircraft-search">Search aircraft</label>
        <input
          id="aircraft-search"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Callsign or ICAO24"
        />
        {filtered.length === 0 ? (
          <p className="muted">No aircraft match that search.</p>
        ) : filtered.map((a) => (
          <AircraftCard key={a.icao24} aircraft={a} active={a.icao24 === selectedIcao} onSelect={onSelect} />
        ))}
      </>
    );
  else if (data && !data.snapshot)
    body = <p className="muted">No saved snapshot yet. Fetch one from the airport panel.</p>;
  else body = null;
  return (
    <section id="aircraft" className="panel">
      <h2>Aircraft{data?.snapshot ? ` (${data.snapshot.position_count})` : ""}</h2>
      {body}
    </section>
  );
}
