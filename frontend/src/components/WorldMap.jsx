import { useEffect, useState } from "react";
import {
  CircleMarker,
  MapContainer,
  Rectangle,
  TileLayer,
  Tooltip,
  useMap,
  useMapEvents,
} from "react-leaflet";

const boundsOf = (area) => [
  [area.lamin, area.lomin],
  [area.lamax, area.lomax],
];

function ViewWatcher({ onChange }) {
  const map = useMap();
  const report = () => onChange(map.getZoom());
  useEffect(report, []);
  useMapEvents({ zoomend: report });
  return null;
}

function FlyTo({ focus }) {
  const map = useMap();
  useEffect(() => {
    if (focus) map.fitBounds(boundsOf(focus), { maxZoom: 11 });
  }, [focus, map]);
  return null;
}

export default function WorldMap({
  airports,
  selected,
  focus,
  aircraft,
  selectedAircraft,
  onSelectAirport,
  onSelectAircraft,
}) {
  const [zoom, setZoom] = useState(2);

  return (
    <div className="map-wrap" aria-label="Map of airports and observed aircraft">
      <MapContainer
        center={[25, 10]}
        zoom={2}
        minZoom={2}
        className="map"
        maxBounds={[[-85, -180], [85, 180]]}
        maxBoundsViscosity={1}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ViewWatcher onChange={setZoom} />
        <FlyTo focus={focus} />

        {selected && (
          <Rectangle
            bounds={boundsOf(selected)}
            pathOptions={{ color: "#d6336c", weight: 2, fillOpacity: 0.12 }}
          />
        )}

        {airports.map((airport) => (
          <CircleMarker
            key={airport.airport_id}
            center={[airport.latitude, airport.longitude]}
            radius={selected?.airport_id === airport.airport_id ? 8 : 5}
            pathOptions={{
              color: selected?.airport_id === airport.airport_id ? "#d6336c" : "#0b7285",
              fillOpacity: 0.9,
            }}
            eventHandlers={{ click: () => onSelectAirport(airport) }}
          >
            <Tooltip>{airport.iata_code} · {airport.city}</Tooltip>
          </CircleMarker>
        ))}

        {aircraft.map((a) => (
          <CircleMarker
            key={a.icao24}
            center={[a.latitude, a.longitude]}
            radius={6}
            pathOptions={{
              color: a.icao24 === selectedAircraft?.icao24 ? "#d6336c" : "#2563eb",
              fillOpacity: 0.9,
            }}
            eventHandlers={{ click: () => onSelectAircraft(a) }}
          >
            <Tooltip>{a.callsign || a.icao24}</Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
      {zoom < 5 && (
        <div className="hint">Select an airport, then zoom in to view aircraft positions.</div>
      )}
    </div>
  );
}
