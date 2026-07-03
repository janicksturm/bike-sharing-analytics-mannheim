import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { RectangleProps } from "recharts";
import type { Station } from "./StationMap";

interface StationRankingChartProps {
  stations: Station[];
  getBarColor: (station: Station) => string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: Station & { displayName: string };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const station = payload[0].payload;
  return (
    <div
      style={{
        background: "#161b22",
        border: "1px solid #30363d",
        borderRadius: 10,
        padding: "10px 14px",
        color: "#e6edf3",
        fontSize: 12,
        fontFamily: "'Inter', sans-serif",
        boxShadow: "0 8px 32px rgba(0,0,0,0.6)",
        minWidth: 170,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 6 }}>{station.name}</div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "auto auto",
          gap: "2px 12px",
        }}
      >
        <span style={{ color: "#8b949e" }}>Bikes</span>
        <span style={{ fontWeight: 700, textAlign: "right" }}>
          {station.bikes}
        </span>
      </div>
    </div>
  );
}

function StationRankingChart({ stations, getBarColor }: StationRankingChartProps) {
  const rankedStations = useMemo(() => {
    const sorted = [...stations].sort((a, b) => b.bikes - a.bikes);
    return sorted.slice(0, 10).map((s) => ({
      ...s,
      displayName: s.name.length > 22 ? s.name.slice(0, 20) + "…" : s.name,
    }));
  }, [stations]);

  if (stations.length === 0) {
    return (
      <div className="bg-gray-800/60 rounded-2xl border border-gray-700 px-6 py-10 flex items-center justify-center">
        <span className="text-sm text-gray-400 animate-pulse">
          Loading station ranking…
        </span>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/60 rounded-2xl border border-gray-700 px-5 pt-4 pb-5">
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={rankedStations}
          layout="vertical"
          margin={{ top: 0, right: 30, left: 10, bottom: 0 }}
          barCategoryGap="20%"
        >
          <XAxis
            type="number"
            tick={{ fill: "#6b7280", fontSize: 11 }}
            axisLine={{ stroke: "#374151" }}
            tickLine={false}
            domain={[0, "auto"]}
          />
          <YAxis
            dataKey="displayName"
            type="category"
            width={160}
            tick={{ fill: "#d1d5db", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            content={<CustomTooltip />}
            cursor={{ fill: "rgba(255,255,255,0.03)" }}
          />
          <Bar
            dataKey="bikes"
            radius={[0, 6, 6, 0]}
            animationDuration={600}
            animationEasing="ease-out"
            shape={(props: RectangleProps & { payload?: Station & { displayName: string } }) => {
              const { x, y, width, height, payload } = props;
              const fill = payload ? getBarColor(payload) : "#6366f1";
              return (
                <rect
                  x={x}
                  y={y}
                  width={width}
                  height={height}
                  fill={fill}
                  rx={6}
                  ry={6}
                />
              );
            }}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default StationRankingChart;
