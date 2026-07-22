
interface StatusCardProps {
  label: string;
  stat: { value: number; delta: number };
  unit?: string;
  decimals?: number;
}

function StatusCard({ label, stat, unit = "", decimals = 0 }: StatusCardProps) {
  const { value, delta } = stat;

  const deltaPositive = delta > 0;
  const deltaNeutral = delta === 0;

  const deltaColor = deltaNeutral
    ? "text-gray-400"
    : deltaPositive
    ? "text-emerald-400"
    : "text-red-400";

  const deltaArrow = deltaNeutral ? "—" : deltaPositive ? "▲" : "▼";
  const deltaAbs = Math.abs(delta);

  return (
    <div className="bg-gray-800 rounded-2xl px-6 py-5 flex flex-col gap-3 shadow-lg border border-gray-700 hover:border-emerald-600 transition-colors duration-200">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">
          {label}
        </span>
      </div>

      <div className="flex items-end gap-2">
        <span className="text-3xl font-bold text-white tracking-tight">
          {value.toFixed(decimals)}
        </span>
        {unit && (
          <span className="text-sm text-gray-400 mb-1">{unit}</span>
        )}
      </div>

      <div className={`flex items-center gap-1 text-xs font-medium ${deltaColor}`}>
        <span>{deltaArrow}</span>
        <span>
          {deltaNeutral
            ? "No change"
            : `${deltaAbs.toFixed(decimals)} ${unit} vs. prev. snapshot`}
        </span>
      </div>
    </div>
  );
}

export default StatusCard;
export type { StatusCardProps };
