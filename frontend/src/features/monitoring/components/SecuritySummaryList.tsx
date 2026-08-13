import type { ServerSecuritySummary } from "@/shared/types/monitoring";
import { SECURITY_CHECK_ROWS } from "../utils";
import { cn } from "@/shared/lib/utils";

interface SecuritySummaryListProps {
  security?: ServerSecuritySummary | null;
  compact?: boolean;
}

function mark(status?: string | null, detail?: string | null) {
  if (status === "ok") {
    return <span className="text-emerald-300">✓{detail ? ` ${detail}` : ""}</span>;
  }
  if (status === "warn" || status === "fail") {
    return (
      <span className="text-amber-300">
        ⚠{detail ? ` ${detail}` : ""}
      </span>
    );
  }
  return <span className="text-brand-600">—</span>;
}

export default function SecuritySummaryList({ security, compact = false }: SecuritySummaryListProps) {
  return (
    <ul className={cn(compact ? "space-y-1.5" : "space-y-2")}>
      {SECURITY_CHECK_ROWS.map(({ key, label }) => {
        const check = security?.[key];
        return (
          <li key={key} className="flex items-center justify-between gap-4 text-sm">
            <span className="text-brand-400">{label}</span>
            {mark(check?.status, check?.detail)}
          </li>
        );
      })}
    </ul>
  );
}
