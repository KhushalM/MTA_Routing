import { MapContainer, TileLayer, Marker, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface RouteMapProps {
  origin: [number, number]; // [lat, lng]
  destination: [number, number];
}

export default function RouteMap({ origin, destination }: RouteMapProps) {
  return (
    <div style={{ height: 300, width: '100%' }}>
      <MapContainer
        center={origin}
        zoom={13}
        style={{ height: '100%', width: '100%', borderRadius: 12 }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={origin} />
        <Marker position={destination} />
        <Polyline positions={[origin, destination]} pathOptions={{ color: 'blue' }} />
      </MapContainer>
    </div>
  );
}

// Lint fix: Ensure file ends with a newline
