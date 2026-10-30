import { useEffect, useRef, useState } from "react";
import {
  getAirportLatest,
  getAirports,
  getDailyObservations,
  importAirport,
} from "./api";
import AircraftDetails from "./components/AircraftDetails";
import AircraftList from "./components/AircraftList";
import AirportPanel from "./components/AirportPanel";
import WorldMap from "./components/WorldMap";

export default function App() {
  const [airports, setAirports] = useState([]);
  const [catalogError, setCatalogError] = useState("");
  const [selected, setSelected] = useState(null);
  const [focus, setFocus] = useState(null);
  const [data, setData] = useState(null);
  const [daily, setDaily] = useState(null);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState("");
  const [aircraft, setAircraft] = useState(null);
  const latest = useRef(0);

  useEffect(() => {
    getAirports()
      .then(setAirports)
      .catch((requestError) => setCatalogError(requestError.message));
  }, []);

  async function selectAirport(airport) {
    const requestId = ++latest.current;
    setSelected(airport);
    setFocus({ ...airport });
    setData(null);
    setDaily(null);
    setAircraft(null);
    setError("");
    setImporting(false);
    setLoading(true);
    try {
      const [latestData, dailyData] = await Promise.all([
        getAirportLatest(airport.airport_id),
        getDailyObservations(airport.airport_id),
      ]);
      if (latest.current === requestId) {
        setData(latestData);
        setDaily(dailyData);
      }
    } catch (requestError) {
      if (latest.current === requestId) setError(requestError.message);
    } finally {
      if (latest.current === requestId) setLoading(false);
    }
  }

  async function fetchSnapshot() {
    if (!selected) return;
    const requestId = latest.current;
    setImporting(true);
    setError("");
    try {
      await importAirport(selected.airport_id);
      const [latestData, dailyData] = await Promise.all([
        getAirportLatest(selected.airport_id),
        getDailyObservations(selected.airport_id),
      ]);
      if (latest.current === requestId) {
        setData(latestData);
        setDaily(dailyData);
      }
    } catch (requestError) {
      if (latest.current === requestId) setError(requestError.message);
    } finally {
      if (latest.current === requestId) setImporting(false);
    }
  }

  const visibleAircraft = (data?.data ?? []).filter((record) => record.has_position);

  return (
    <>
      <header>
        <h1>Airzone</h1>
        <nav aria-label="Main navigation">
          <a href="#map">Map</a>
          <a href="#airport">Airport analysis</a>
          <a href="#aircraft">Aircraft</a>
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            API docs
          </a>
        </nav>
      </header>
      <main>
        <div id="map" className="map-col">
          <WorldMap
            airports={airports}
            selected={selected}
            focus={focus}
            aircraft={visibleAircraft}
            selectedAircraft={aircraft}
            onSelectAirport={selectAirport}
            onSelectAircraft={setAircraft}
          />
          {aircraft && (
            <AircraftDetails
              aircraft={aircraft}
              airportId={selected.airport_id}
              onClose={() => setAircraft(null)}
            />
          )}
        </div>
        <aside>
          <div id="airport">
            <AirportPanel
              airports={airports}
              catalogError={catalogError}
              selected={selected}
              data={data}
              daily={daily}
              loading={loading}
              importing={importing}
              error={error}
              onSelect={selectAirport}
              onImport={fetchSnapshot}
            />
          </div>
          <AircraftList
            airport={selected}
            data={data}
            loading={loading}
            error={error}
            selectedIcao={aircraft?.icao24}
            onSelect={setAircraft}
          />
        </aside>
      </main>
    </>
  );
}
