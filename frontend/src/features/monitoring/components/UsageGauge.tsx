import { cn } from "@/shared/lib/utils";
import { usageTone } from "../utils";

interface UsageGaugeProps {
  label: string;
  value?: number | null;
  detail?: string;
}

const toneFill = {
  default: "bg-emerald-500/80",
  warning: "bg-amber-500/80",
  danger: "bg-orange-500/80",
  critical: "bg-rose-500/80",
};

export default function UsageGauge({ label, value, detail }: UsageGaugeProps) {
  const tone = usageTone(value);
  const width = Math.max(0, Math.min(100, value ?? 0));

  return (
    <div className="glass-panel p-5">
      <p className="terminal-text text-xs text-brand-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold tabular-nums text-brand-50">
        {value == null ? "—" : `${value.toFixed(0)}%`}
      </p>
      {detail && <p className="mt-1 text-xs text-brand-500">{detail}</p>}
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-void-100/80">
        <div
          className={cn("h-full rounded-full transition-all", toneFill[tone])}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}
