import { useState, useEffect } from "react";
import useFetch from "../hooks/useFetch";
import useGeolocation from "../hooks/useGeolocation";
import RecommendationMap from "../components/RecommendationMap";
import RecommendationCard from "../components/RecommendationCard";
import type { Recommendation } from "../components/RecommendationMap";

interface StationBasic {
  uid: number;
  name: string;
  lat: number;
  lng: number;
  bikes: number;
  status: string;
}

interface StationsResponse {
  stations: StationBasic[];
}

interface RecommendationResponse {
  user_location?: { lat: number; lng: number };
  recommendations: Recommendation[];
}

function PredictionPage() {
  const geo = useGeolocation();
  const [stationsData] = useFetch<StationsResponse>("http://localhost:8000/stations");

  // Recommendation state
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [recLoading, setRecLoading] = useState(false);
  const [gpsMode, setGpsMode] = useState(true);

  // GPS-based recommendations
  useEffect(() => {
    if (!geo.loading && geo.lat !== null && geo.lng !== null) {
      setRecLoading(true);
      fetch("http://localhost:8000/recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lat: geo.lat, lng: geo.lng }),
      })
        .then((res) => res.json())
        .then((data: RecommendationResponse) => {
          setRecommendations(data.recommendations || []);
          setGpsMode(true);
        })
        .catch(() => setRecommendations([]))
        .finally(() => setRecLoading(false));
    } else if (!geo.loading && geo.error) {
      setGpsMode(false);
    }
  }, [geo.loading, geo.lat, geo.lng, geo.error]);

  return (
    <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
      <section>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-white">Recommended Stations</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {gpsMode && geo.lat
                ? "Based on your current location"
                : "Click a station on the map to get alternatives"}
            </p>
          </div>

          {/* GPS Status Badge */}
          <div className="flex items-center gap-2">
            {geo.loading ? (
              <span className="flex items-center gap-2 text-xs text-blue-400">
                <span className="inline-block h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
                Locating…
              </span>
            ) : geo.lat ? (
              <span className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-400/10 px-3 py-1.5 rounded-full">
                <span className="inline-block h-2 w-2 rounded-full bg-emerald-400" />
                GPS Active
              </span>
            ) : (
              <span className="flex items-center gap-2 text-xs text-yellow-400 bg-yellow-400/10 px-3 py-1.5 rounded-full">
                <span className="inline-block h-2 w-2 rounded-full bg-yellow-400" />
                Manual Mode
              </span>
            )}
          </div>
        </div>

        {/* Recommendation Map */}
        <RecommendationMap
          recommendations={recommendations}
          allStations={stationsData?.stations || []}
          userLat={gpsMode ? geo.lat : null}
          userLng={gpsMode ? geo.lng : null}
        />

        {/* Recommendation Cards */}
        {recLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-4 mt-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="bg-gray-800 rounded-2xl h-52 animate-pulse border border-gray-700"
              />
            ))}
          </div>
        ) : recommendations.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-4 mt-4">
            {recommendations.map((rec) => (
              <RecommendationCard
                key={rec.uid}
                recommendation={rec}
              />
            ))}
          </div>
        ) : !geo.loading ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-gray-700 bg-gray-800/50 py-16 px-8 mt-4">
            <p className="text-sm text-gray-400 text-center max-w-md">
              {gpsMode
                ? "No recommendations available for your location."
                : "Click on any station on the map above to see recommended alternatives."}
            </p>
          </div>
        ) : null}
      </section>
    </main>
  );
}

export default PredictionPage;
