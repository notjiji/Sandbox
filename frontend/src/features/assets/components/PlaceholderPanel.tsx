import { Clock } from "lucide-react";

interface PlaceholderPanelProps {
  title: string;
  description: string;
  phase?: string;
}

export default function PlaceholderPanel({ title, description, phase }: PlaceholderPanelProps) {
  return (
    <div className="glass-panel p-6">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-brand-100">{title}</h2>
        {phase && (
          <span className="rounded-full border border-brand-700/50 bg-brand-900/40 px-2.5 py-0.5 text-xs text-brand-400">
            {phase}
          </span>
        )}
      </div>
      <div className="flex items-start gap-3 rounded-lg border border-dashed border-brand-800/60 bg-brand-950/20 px-4 py-5">
        <Clock size={18} className="mt-0.5 shrink-0 text-brand-500" />
        <div>
          <p className="text-sm text-brand-300">{description}</p>
          <p className="mt-1 text-xs text-brand-500">Not available yet</p>
        </div>
      </div>
    </div>
  );
}
