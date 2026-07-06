import type { Recommendation } from "./RecommendationMap";

interface RecommendationCardProps {
  recommendation: Recommendation;
}

function RecommendationCard({ recommendation: rec }: RecommendationCardProps) {
  const isBestPick = rec.rank === 1;

  return (
    <div
      className={`bg-gray-800 rounded-2xl px-5 py-4 border duration-200 ${
        isBestPick
          ? "border-emerald-500/60 shadow-emerald-500/20"
          : "border-gray-700"
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <span
          className={`recommendation-rank-badge recommendation-rank-${rec.rank}`}
        >
          #{rec.rank}
        </span>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-white truncate">{rec.name}</div>
        </div>
        <span className="text-xs text-gray-400">
          {rec.distance_meters.toFixed(0)}m
        </span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div>
          <div className="text-[10px] text-gray-400 uppercase">Bikes</div>
          <div className="text-lg font-bold text-white">{rec.bikes}</div>
        </div>
        <div>
          <div className="text-[10px] text-gray-400 uppercase">Empty Rate</div>
          <div className="text-lg font-bold text-white">{rec.empty_rate.toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-[10px] text-gray-400 uppercase">Occ.</div>
          <div className="text-lg font-bold text-white">{rec.occupancy_pct}%</div>
        </div>
      </div>

      {/* Score bar */}
      <div className="mb-2">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-gray-400 uppercase">Score</span>
          <span className="text-xs font-bold text-emerald-400">{rec.recommendation_score.toFixed(1)}</span>
        </div>
        <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${Math.min(100, Math.max(5, rec.recommendation_score))}%`,
              background: `linear-gradient(90deg, #10b981, #34d399)`,
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default RecommendationCard;
