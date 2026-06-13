import useFetch from "./hooks/useFetch";
import Header from "./components/Header";
import StatusCard from "./components/StatusCard";
import type { StatValue } from "./components/StatusCard";
import "./App.css";

interface KpiSnapshot {
  snapshot_time: string;
  total_bikes: StatValue;
  available_to_rent: StatValue;
  empty_stations: StatValue;
  avg_occupancy: StatValue;
}

function formatSnapshotTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function App() {
  const [data] = useFetch<KpiSnapshot>("http://localhost:8000/status");

  return (
    <div className="min-h-screen bg-gray-900">
      <Header />

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Status</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              {data
                ? `Snapshot: ${formatSnapshotTime(data.snapshot_time)}`
                : "Fetching latest snapshot…"}
            </p>

          {!data && (
            <span className="flex items-center gap-2 text-xs text-emerald-400">
              <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              Loading…
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {!data
            ? Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="bg-gray-800 rounded-2xl px-6 py-5 h-36 animate-pulse border border-gray-700"
              />
            ))
            : (
              <>
                <StatusCard
                  label="Total Bikes"
                  stat={data.total_bikes}
                />
                <StatusCard
                  label="Available to Rent"
                  stat={data.available_to_rent}
                />
                <StatusCard
                  label="Empty Stations"
                  stat={data.empty_stations}
                />
                <StatusCard
                  label="Avg Occupancy"
                  stat={data.avg_occupancy}
                  unit="%"
                  decimals={1}
                />
              </>
            )}
        </div>
      </main>
    </div>
  );
}

export default App;