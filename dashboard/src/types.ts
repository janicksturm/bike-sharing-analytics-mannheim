// ── Shared type definitions ──────────────────────────────────────────────────

/** Station data returned by the /stations endpoint. */
export interface Station {
  uid: number;
  name: string;
  lat: number;
  lng: number;
  bike_racks: number | null;
  bikes: number | null;
  free_racks: number | null;
  occupancy_pct: number | null;
}

/** A scored station recommendation from the backend. */
export interface Recommendation {
  rank: number;
  uid: number;
  name: string;
  lat: number;
  lng: number;
  bikes: number;
  free_racks: number;
  occupancy_pct: number;
  distance_meters: number;
  empty_rate: number;
  demand_score: number | null;
  recommendation_score: number;
}

/** Shape of the /status response. */
export interface KpiSnapshot {
  snapshot_time: string;
  total_bikes: number;
  total_bikes_delta: number | null;
  empty_stations: number;
  empty_stations_delta: number | null;
  avg_occupancy: number;
  avg_occupancy_delta: number | null;
}

/** Shape of the /recommendations response. */
export interface RecommendationResponse {
  recommendations: Recommendation[];
}
