import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, Rectangle, TileLayer, Tooltip, useMap, useMapEvents } from "react-leaflet";

const CELL = 4;               // must match CELL in backend/database.py
const ROWS = 180 / CELL;
const COLS = 360 / CELL;
const MIN_ZOOM_FOR_GRID = 4;  // below this, too many cells would be drawn
const MAX_CELLS = 400;

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const cellToZone = (row, col) => {
  const lamin = row * CELL - 90, lomin = col * CELL - 180;
  return { zone_id: `R${row}C${col}`, name: `Grid R${row}C${col}`, lamin, lomin, lamax: lamin + CELL, lomax: lomin + CELL };
};
const style = (selected) => ({
  color: selected ? "#d6336c" : "#3b82f6",
  weight: selected ? 3 : 1,
  fillOpacity: selected ? 0.25 : 0.04,
  interactive: !selected,
});
// Leaflet wants [latitude, longitude]. (GeoJSON would be [longitude, latitude].)
const boundsOf = (z) => [[z.lamin, z.lomin], [z.lamax, z.lomax]];

function ViewWatcher({ onChange }) {
  const map = useMap();
  const report = () => onChange({ bounds: map.getBounds(), zoom: map.getZoom() });
  useEffect(report, []);
  useMapEvents({ moveend: report });
  return null;
}

function FlyTo({ focus }) {
  const map = useMap();
  useEffect(() => { if (focus) map.fitBounds(boundsOf(focus), { maxZoom: 6 }); }, [focus]);
  return null;
}

export default function WorldMap({ selected, focus, aircraft, selectedAircraft, onSelectZone, onSelectAircraft }) {
  const [view, setView] = useState(null);

  // Only build cells that are inside the visible map area.
  const cells = [];
  if (view && view.zoom >= MIN_ZOOM_FOR_GRID) {
    const b = view.bounds;
    const r0 = clamp(Math.floor((b.getSouth() + 90) / CELL), 0, ROWS - 1);
    const r1 = clamp(Math.floor((b.getNorth() + 90) / CELL), 0, ROWS - 1);
    const c0 = clamp(Math.floor((b.getWest() + 180) / CELL), 0, COLS - 1);
    const c1 = clamp(Math.floor((b.getEast() + 180) / CELL), 0, COLS - 1);
    if ((r1 - r0 + 1) * (c1 - c0 + 1) <= MAX_CELLS)
      for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) cells.push(cellToZone(r, c));
  }

  return (
    <div className="map-wrap">
      <MapContainer center={[20, 40]} zoom={4} minZoom={2} className="map"
        maxBounds={[[-90, -180], [90, 180]]} maxBoundsViscosity={1}>
        <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <ViewWatcher onChange={setView} />
        <FlyTo focus={focus} />

        {cells.filter((z) => z.zone_id !== selected?.zone_id).map((z) => (
          <Rectangle key={z.zone_id} bounds={boundsOf(z)} pathOptions={style(false)}
            eventHandlers={{
              click: () => onSelectZone(z),
              mouseover: (e) => e.target.setStyle({ fillOpacity: 0.3, weight: 2 }),
              mouseout: (e) => e.target.setStyle(style(false)),
            }}>
            <Tooltip sticky>{z.zone_id}</Tooltip>
          </Rectangle>
        ))}

        {selected && <Rectangle key={"sel" + selected.zone_id} bounds={boundsOf(selected)} pathOptions={style(true)} />}

        {aircraft.map((a) => (
          <CircleMarker key={a.icao24} center={[a.latitude, a.longitude]} radius={6}
            pathOptions={{ color: a.icao24 === selectedAircraft?.icao24 ? "#d6336c" : "#0b7285", fillOpacity: 0.85 }}
            eventHandlers={{ click: () => onSelectAircraft(a) }}>
            <Tooltip>{a.callsign || a.icao24}</Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
      {(!view || view.zoom < MIN_ZOOM_FOR_GRID) && <div className="hint">Zoom in to see selectable airzones</div>}
    </div>
  );
}
