import { useMemo, useState } from "react";
import { when } from "../api";

export default function AirportPanel({
  airports,
  catalogError,
  selected,
  data,
  daily,
  loading,
  importing,
  error,
  onSelect,
  onImport,
}) {
  const [query, setQuery] = useState("");
  const matches = useMemo(() => {
    const term = query.trim().toLocaleLowerCase();
    if (!term) return airports;
    return airports.filter((airport) =>
      [airport.iata_code, airport.name, airport.city, airport.country]
        .join(" ")
        .toLocaleLowerCase()
        .includes(term),
    );
  }, [airports, query]);
  const dailyRows = daily?.days ?? [];
  const noSamples = dailyRows.length > 0 &&
    dailyRows.every((entry) => entry.sample_count === 0);
  const maxCount = Math.max(
    1,
    ...dailyRows.map((entry) => entry.observed_aircraft_count ?? 0),
  );

  return (
    <section className="panel airport-panel">
      <h2>Airport traffic</h2>
      <label htmlFor="airport-search">Find an airport</label>
      <input
        id="airport-search"
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search airport, city, or IATA code"
        aria-describedby="airport-catalog-note"
      />
      <p id="airport-catalog-note" className="muted">
        Search by name, city, or code. Includes India’s designated international
        airports and a selected set of airports worldwide.
      </p>
      {catalogError && <p className="error" role="alert">{catalogError}</p>}
      {airports.length > 0 && (
        <div className="airport-results" aria-label="Airport search results">
          {matches.map((airport) => (
            <button
              className={`airport-option${selected?.airport_id === airport.airport_id ? " active" : ""}`}
              key={airport.airport_id}
              onClick={() => onSelect(airport)}
              aria-pressed={selected?.airport_id === airport.airport_id}
            >
              <span>
                <b>{airport.name}</b>
                <small>{airport.city}, {airport.country}</small>
              </span>
              <span className="airport-code">
                <small>{airport.airport_type}</small>
                <code>{airport.iata_code}</code>
              </span>
            </button>
          ))}
          {matches.length === 0 && (
            <p className="muted">No airports match that search.</p>
          )}
        </div>
      )}

      {selected && (
        <div className="airport-summary">
          <h3>{selected.name}</h3>
          <p className="muted">
            {selected.city}, {selected.country} · {selected.iata_code}
          </p>
          <p className="muted">
            The map shows an approximate 22 km × 22 km square centered on this
            airport’s marked reference point.
          </p>
          <button onClick={onImport} disabled={importing || loading}>
            {importing ? "Fetching snapshot…" : "Fetch latest snapshot"}
          </button>
          {error && <p className="error" role="alert">{error}</p>}
          {loading && <p className="state" role="status">Loading saved airport data…</p>}
          {data?.snapshot ? (
            <div className="snapshot-summary">
              <b>{data.snapshot.position_count} aircraft with positions</b>
              <span className="muted">
                Snapshot: {when(data.snapshot.provider_time)}
              </span>
              <span className="muted">
                {data.snapshot.state_count} states returned by OpenSky
              </span>
            </div>
          ) : !loading ? (
            <p className="muted">No snapshot saved yet. Fetch one to begin.</p>
          ) : null}
          {daily && (
            <div className="daily-summary">
              <h3>Daily observed aircraft</h3>
              <p className="muted">
                Distinct aircraft with positions in stored manual samples (UTC).
                This is not a flight-movement count.
              </p>
              {noSamples && (
                <div className="daily-empty" role="status">
                  <b>No observations have been sampled yet.</b>
                  <p>
                    Select <strong>Fetch latest snapshot</strong> above to collect
                    the first sample. Daily results build from snapshots you
                    manually collect; a day with no samples is unknown, not zero.
                  </p>
                </div>
              )}
              <ul className="daily-list">
                {dailyRows.map((entry) => (
                  <li key={entry.day}>
                    <span className="daily-date">{entry.day}</span>
                    <span
                      className="daily-bar"
                      role="meter"
                      aria-label={`${entry.day}: ${entry.observed_aircraft_count ?? "no data"}`}
                      aria-valuemin="0"
                      aria-valuemax={maxCount}
                      aria-valuenow={entry.observed_aircraft_count ?? 0}
                    >
                      <span
                        style={{
                          width: `${((entry.observed_aircraft_count ?? 0) / maxCount) * 100}%`,
                        }}
                      />
                    </span>
                    <b>
                      {entry.observed_aircraft_count === null
                        ? "No samples"
                        : entry.observed_aircraft_count}
                    </b>
                    <small>{entry.sample_count} sample{entry.sample_count === 1 ? "" : "s"}</small>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
