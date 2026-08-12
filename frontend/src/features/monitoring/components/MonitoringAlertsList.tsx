import type { AlertSummary } from "@/shared/types/monitoring";
import { severityClass } from "../utils";

interface MonitoringAlertsListProps {
  alerts: AlertSummary[];
}

export default function MonitoringAlertsList({ alerts }: MonitoringAlertsListProps) {
  if (alerts.length === 0) {
    return <p className="text-sm text-brand-600">No monitoring alerts yet.</p>;
  }

  return (
    <ul className="space-y-3">
      {alerts.map((alert) => (
        <li
          key={alert.id}
          className={`rounded-lg border px-4 py-3 ${severityClass(alert.severity)} ${
            alert.status === "resolved" ? "opacity-60" : ""
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-medium">{alert.title}</p>
              {alert.message && <p className="mt-1 text-xs opacity-80">{alert.message}</p>}
            </div>
            <span className="shrink-0 text-[10px] uppercase tracking-wider">
              {alert.status} · {alert.severity}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}
