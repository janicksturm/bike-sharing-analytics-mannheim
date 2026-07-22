import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Recommendation, StationBasic } from "../types";

interface RecommendationMapProps {
  recommendations: Recommendation[];
  allStations: StationBasic[];
  userLat: number | null;
  userLng: number | null;
  onStationClick?: (uid: number) => void;
  selectedStationUid?: number | null;
}

const RANK_COLORS = ["#10b981", "#34d399", "#6ee7b7", "#a7f3d0", "#d1fae5"];

function createRecommendationPopup(r: Recommendation): string {
  const scorePct = Math.round(r.recommendation_score * 100);
  return `
    <div class="font-sans min-w-[200px] text-gray-200 bg-gray-900 rounded-xl px-3.5 py-3">
      <div class="flex items-center gap-2 mb-1">
        <span class="recommendation-rank-badge recommendation-rank-${r.rank}">#${r.rank}</span>
        <b class="text-sm text-white">${r.name}</b>
      </div>
      <hr class="my-1.5 border-t border-gray-700" />
      <table class="w-full text-xs border-collapse">
        <tr>
          <td class="text-gray-400 py-0.5">Bikes</td>
          <td class="text-right font-bold text-white">${r.bikes}</td>
        </tr>
        <tr>
          <td class="text-gray-400 py-0.5">Free Racks</td>
          <td class="text-right font-bold text-white">${r.free_racks}</td>
        </tr>
        <tr>
          <td class="text-gray-400 py-0.5">Occupancy</td>
          <td class="text-right font-bold text-white">${r.occupancy_pct}%</td>
        </tr>
        <tr>
          <td class="text-gray-400 py-0.5">Distance</td>
          <td class="text-right font-bold text-white">${r.distance_meters.toFixed(0)}m</td>
        </tr>
        <tr>
          <td class="text-gray-400 py-0.5">Empty Rate</td>
          <td class="text-right font-bold text-white">${r.empty_rate.toFixed(1)}%</td>
        </tr>
        <tr>
          <td class="text-gray-400 py-0.5">Score</td>
          <td class="text-right font-bold text-emerald-400">${scorePct}%</td>
        </tr>
      </table>
    </div>`;
}

function RecommendationMap({recommendations, allStations, userLat, userLng, onStationClick, selectedStationUid, }: RecommendationMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMap = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Layer[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  // Initialize map (once)
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

  // Re-center map when user location becomes available
  useEffect(() => {
    const map = leafletMap.current;
    if (!map || !isLoaded) return;
    if (userLat !== null && userLng !== null) {
      map.setView([userLat, userLng], 15, { animate: true });
    }
  }, [userLat, userLng, isLoaded]);

  // Sync markers
  useEffect(() => {
    const map = leafletMap.current;
    if (!map || !isLoaded) return;

    // Clear old markers
    markersRef.current.forEach((m) => map.removeLayer(m));
    markersRef.current = [];

    const recommendedUids = new Set(recommendations.map((r) => r.uid));

    // Draw all stations as small gray dots with lightgray highlighting
    allStations.forEach((station) => {
      if (recommendedUids.has(station.uid)) return;

      const isSelected = station.uid === selectedStationUid;
      const marker = L.circleMarker([station.lat, station.lng], {
        radius: isSelected ? 8 : 4,
        color: isSelected ? "#3b82f6" : "#aeb3ba",
        weight: isSelected ? 2 : 1,
        fillColor: isSelected ? "#3b82f6" : "#4b5563",
        fillOpacity: isSelected ? 0.9 : 0.3,
      });

      marker.bindTooltip(`${station.name} · ${station.bikes} bikes`, {
        sticky: true,
        className: "leaflet-custom-tooltip",
      });

      if (onStationClick) {
        marker.on("click", () => onStationClick(station.uid));
      }

      marker.addTo(map);
      markersRef.current.push(marker);
    });

    // Draw user position
    if (userLat !== null && userLng !== null) {
      const userMarker = L.circleMarker([userLat, userLng], {
        radius: 10,
        color: "#3b82f6",
        weight: 3,
        fillColor: "#3b82f6",
        fillOpacity: 0.4,
        className: "user-location-marker",
      });
      userMarker.bindTooltip("Your Location", {
        permanent: false,
        className: "leaflet-custom-tooltip",
      });
      userMarker.addTo(map);
      markersRef.current.push(userMarker);

      // Outer pulse ring
      const pulseRing = L.circleMarker([userLat, userLng], {
        radius: 18,
        color: "#3b82f6",
        weight: 1.5,
        fillColor: "#3b82f6",
        fillOpacity: 0.1,
        className: "user-pulse-ring",
      });
      pulseRing.addTo(map);
      markersRef.current.push(pulseRing);
    }

    // Draw recommended stations with rank markers
    recommendations.forEach((rec) => {
      const color = RANK_COLORS[rec.rank - 1] || RANK_COLORS[4];
      const radius = rec.rank === 1 ? 12 : 9;

      const marker = L.circleMarker([rec.lat, rec.lng], {
        radius,
        color: "#1f2937",
        weight: 2,
        fillColor: color,
        fillOpacity: 0.9,
        className: rec.rank === 1 ? "best-pick-marker" : "",
      });

      marker.bindPopup(
        L.popup({ maxWidth: 260, className: "leaflet-custom-popup" })
          .setContent(createRecommendationPopup(rec))
      );

      marker.bindTooltip(`#${rec.rank} ${rec.name}`, {
        sticky: true,
        className: "leaflet-custom-tooltip",
      });

      marker.addTo(map);
      markersRef.current.push(marker);

      // Dashed line from user/selected station to recommendation
      const originLat = userLat ?? (selectedStationUid ? allStations.find(s => s.uid === selectedStationUid)?.lat : null);
      const originLng = userLng ?? (selectedStationUid ? allStations.find(s => s.uid === selectedStationUid)?.lng : null);

      if (originLat != null && originLng != null) {
        const line = L.polyline(
          [[originLat, originLng], [rec.lat, rec.lng]],
          {
            color,
            weight: 1.5,
            opacity: rec.rank === 1 ? 0.7 : 0.3,
            dashArray: "6 8",
          }
        );
        line.addTo(map);
        markersRef.current.push(line);
      }
    });
  }, [recommendations, allStations, userLat, userLng, isLoaded, selectedStationUid, onStationClick]);

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

export default RecommendationMap;
