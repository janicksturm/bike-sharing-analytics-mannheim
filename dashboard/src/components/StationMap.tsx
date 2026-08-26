import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Station } from "../types";

interface StationMapProps {
  stations: Station[];
}

function getMarkerColor(pct: number): string {
  if (pct >= 90) return "#ef4444";
  if (pct >= 60) return "#f59e0b";
  return "#22c55e";
}

function createCircleMarker(station: Station) {
  return L.circleMarker([station.lat, station.lng], {
    radius: 6,
    color: "#1f2937",
    weight: 1.5,
    fillColor: getMarkerColor(station.occupancy_pct != null ? Math.round(station.occupancy_pct * 100) : 0),
    fillOpacity: 0.9,
  });
}

function createPopupContent(s: Station): string {
  return `
    <div class="font-sans min-w-[190px] text-gray-200 bg-gray-900 rounded-xl px-3.5 py-3">
      <b class="text-sm text-white">${s.name}</b>
      <hr class="my-1.5 border-t border-gray-700" />
      <table class="w-full text-xs border-collapse">
        <tr>
          <td class="text-gray-400 py-0.5">Total racks</td>
          <td class="text-right font-bold text-white">${s.bike_racks ?? '—'}</td>
        </tr>
      </table>
    </div>`;
}

/**
 * Initializes the Leaflet map and handles its lifecycle (cleanup on unmount).
 */
function useMapInitialization(mapRef: React.RefObject<HTMLDivElement | null>) {
  const leafletMap = useRef<L.Map | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    if (!mapRef.current || leafletMap.current) return;

    const map = L.map(mapRef.current, {
      center: [49.4875, 8.4660],
      zoom: 14,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; OpenStreetMap &copy; CartoDB',
      maxZoom: 30,
    }).addTo(map);

    leafletMap.current = map;
    setIsLoaded(true);

    return () => {
      map.remove();
      leafletMap.current = null;
    };
  }, []);

  return { leafletMap, isLoaded };
}

/**
 * Re-centers the map to fit all station bounds once stations are loaded.
 */
function useMapFitStations(leafletMap: React.RefObject<L.Map | null>, isLoaded: boolean, stations: Station[]) {
  const hasFitted = useRef(false);

  useEffect(() => {
    const map = leafletMap.current;
    if (!map || !isLoaded || stations.length === 0 || hasFitted.current) return;

    const bounds = L.latLngBounds(stations.map((s) => [s.lat, s.lng]));
    map.fitBounds(bounds, { padding: [30, 30], animate: false });
    hasFitted.current = true;
  }, [stations, isLoaded, leafletMap]);
}

/**
 * Syncs the station array with the Leaflet map by drawing and removing markers.
 */
function useMapMarkers(leafletMap: React.RefObject<L.Map | null>, isLoaded: boolean, stations: Station[]) {
  const markersRef = useRef<L.CircleMarker[]>([]);

  useEffect(() => {
    const map = leafletMap.current;
    if (!map || !isLoaded || !Array.isArray(stations)) return;

    // Clear old markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Draw new markers
    stations.forEach((station) => {
      const marker = createCircleMarker(station);
      marker.bindPopup(L.popup({ maxWidth: 240, className: "leaflet-custom-popup" }).setContent(createPopupContent(station)));
      marker.bindTooltip(station.name, {
        sticky: true,
        className: "leaflet-custom-tooltip",
      });
      marker.addTo(map);
      markersRef.current.push(marker);
    });
  }, [stations, isLoaded, leafletMap]);
}

function StationMap({ stations }: StationMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);

  const { leafletMap, isLoaded } = useMapInitialization(mapRef);

  // Fit map to stations once they arrive
  useMapFitStations(leafletMap, isLoaded, stations);

  // Sync station markers dynamically
  useMapMarkers(leafletMap, isLoaded, stations);

  return (
    <div className="relative rounded-2xl overflow-hidden border border-gray-700 shadow-xl" style={{ height: 420 }}>
      <div ref={mapRef} className="w-full h-full" />

      {!isLoaded && (
        <div className="absolute inset-0 bg-gray-900 flex items-center justify-center">
          <span className="text-sm text-gray-400 animate-pulse">Loading map…</span>
        </div>
      )}
    </div>
  );
}

export default StationMap;