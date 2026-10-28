import { useEffect, useRef, useState } from "react";
import { getZoneAircraft, getZones } from "./api";
import WorldMap from "./components/WorldMap";
import ZoneDetails from "./components/ZoneDetails";
import AircraftList from "./components/AircraftList";
import AircraftDetails from "./components/AircraftDetails";

export default function App() {
  const [zones, setZones] = useState([]);
  const [selected, setSelected] = useState(null);   
  const [focus, setFocus] = useState(null);         
  const [data, setData] = useState(null);           
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [aircraft, setAircraft] = useState(null);   
  const latest = useRef("");                        

  useEffect(() => {
    getZones().then(setZones).catch((e) => setError(e.message));
  }, []);

  async function load(zone) {
    latest.current = zone.zone_id;
    setLoading(true);
    setError("");
    setAircraft(null);
    try {
      const result = await getZoneAircraft(zone.zone_id);
      if (latest.current === zone.zone_id) setData(result);
    } catch (e) {
      if (latest.current === zone.zone_id) { setData(null); setError(e.message); }
    } finally {
      if (latest.current === zone.zone_id) setLoading(false);
    }
  }

  function selectZone(zone, fromList = false) {
    setSelected(zone);
    if (fromList) setFocus({ ...zone });
    load(zone);
  }

  const visible = data ? data.aircraft.filter((a) => a.has_position) : [];

  return (
    <>
      <header>
        <h1>Airzone</h1>
        <nav>
          <a href="#map">Map</a>
          <a href="#aircraft">Aircraft</a>
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">API docs</a>
        </nav>
      </header>
      <main>
        <div id="map" className="map-col">
          <WorldMap selected={selected} focus={focus} aircraft={visible} selectedAircraft={aircraft}
            onSelectZone={(z) => selectZone(z)} onSelectAircraft={setAircraft} />
               {aircraft && <AircraftDetails aircraft={aircraft} onClose={() => setAircraft(null)} />}
        </div>
        <aside>
          <ZoneDetails zone={selected} data={data} loading={loading}
            presets={zones.filter((z) => !/^R\d+C\d+$/.test(z.zone_id))}
            onPick={(z) => selectZone(z, true)} onRefresh={() => selected && load(selected)} />
          <AircraftList zone={selected} data={data} loading={loading} error={error}
            selectedIcao={aircraft?.icao24} onSelect={setAircraft} />
        </aside>
      </main>
    </>
  );
}
