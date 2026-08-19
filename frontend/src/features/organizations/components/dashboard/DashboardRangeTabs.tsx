import { cn } from "@/shared/lib/utils";

interface DashboardRangeTabsProps {
  value: number;
  onChange: (value: number) => void;
}

const RANGES = [
  { value: 7, label: "7 days" },
  { value: 30, label: "30 days" },
  { value: 90, label: "90 days" },
  { value: 365, label: "1 year" },
] as const;

export default function DashboardRangeTabs({ value, onChange }: DashboardRangeTabsProps) {
  return (
    <div className="inline-flex rounded-xl border border-brand-800/60 bg-brand-900/50 p-1">
      {RANGES.map((range) => (
        <button
          key={range.value}
          type="button"
          onClick={() => onChange(range.value)}
          className={cn(
            "rounded-lg px-3 py-1.5 text-xs font-medium transition",
            value === range.value
              ? "bg-brand-700 text-brand-50 shadow-sm"
              : "text-brand-400 hover:bg-brand-800/60 hover:text-brand-200",
          )}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
}
