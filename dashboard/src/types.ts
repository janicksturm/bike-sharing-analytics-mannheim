// ── Shared type definitions ──────────────────────────────────────────────────

/** Station data returned by the /stations endpoint (full detail). */
export interface Station {
  uid: number;
  name: string;
  lat: number;
  lng: number;
  bikes: number;
  free_racks: number;
  occupancy_pct: number;
  bikes_available_to_rent: number;
  status: "Available" | "Low" | "Empty";
}

/** Minimal station info used in pages that don't need every field. */
export interface StationBasic {
  uid: number;
  name: string;
  lat: number;
  lng: number;
  bikes: number;
  status: string;
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
  status: string;
  distance_meters: number;
  empty_rate: number;
  recommendation_score: number;
}

/** KPI value + delta vs. previous snapshot. */
export interface StatValue {
  value: number;
  delta: number;
}

/** Shape of the /status response. */
export interface KpiSnapshot {
  snapshot_time: string;
  total_bikes: StatValue;
  available_to_rent: StatValue;
  empty_stations: StatValue;
  avg_occupancy: StatValue;
}

/** Shape of the /stations response. */
export interface StationResponse {
  stations: Station[];
}

/** Shape of the /recommendations response. */
export interface RecommendationResponse {
  user_location?: { lat: number; lng: number };
  recommendations: Recommendation[];
}
