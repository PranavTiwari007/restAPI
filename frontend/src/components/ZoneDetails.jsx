import { when } from "../api";

export default function ZoneDetails({ zone, data, loading, presets, onPick, onRefresh }) {
  return (
    <section className="panel">
      <h2>Selected zone</h2>
      {zone ? (
        <>
          <p><b>{zone.name}</b> <code>{zone.zone_id}</code></p>
          <p className="muted">
            lamin {zone.lamin}, lomin {zone.lomin}<br />lamax {zone.lamax}, lomax {zone.lomax}
          </p>
          <button onClick={onRefresh} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
          {data && (
            <p className="muted">
              Snapshot: {when(data.time)}<br />
              {data.cached ? "Served from cache (no credits used)." : `Fresh fetch, ${data.saved} new observations saved.`}<br />
              Credits used today (estimate): {data.credits_used_today}
              {data.credits_remaining !== null && ` · remaining reported by OpenSky: ${data.credits_remaining}`}
            </p>
          )}
        </>
      ) : (
        <p className="muted">Click a cell on the map (zoom in first) or pick a quick zone.</p>
      )}
      <h3>Quick zones</h3>
      <div className="chips">
        {presets.map((z) => <button key={z.zone_id} className="chip" onClick={() => onPick(z)}>{z.name}</button>)}
      </div>
    </section>
  );
}
