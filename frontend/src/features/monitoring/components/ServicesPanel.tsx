import type { ServiceInfo } from "@/shared/types/monitoring";
import { cn } from "@/shared/lib/utils";

interface ServicesPanelProps {
  services?: ServiceInfo[];
}

function statusClass(status: string): string {
  const value = status.toUpperCase();
  if (value === "RUNNING") return "text-emerald-300";
  if (value === "FAILED") return "text-rose-300";
  if (value === "STOPPED" || value === "INACTIVE") return "text-brand-500";
  return "text-brand-300";
}

export default function ServicesPanel({ services = [] }: ServicesPanelProps) {
  if (services.length === 0) {
    return (
      <p className="text-sm text-brand-600">
        Running services will appear after the first heartbeat (Linux systemd).
      </p>
    );
  }

  return (
    <div>
      <ul className="max-h-72 space-y-1 overflow-y-auto font-mono text-sm">
        {services.map((service) => (
          <li key={service.name} className="flex items-center justify-between gap-4 py-1">
            <span className="truncate text-brand-100">{service.name}</span>
            <span className={cn("shrink-0 tracking-wide", statusClass(service.status))}>
              {service.status.toUpperCase()}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-brand-600">
        {services.length} service{services.length === 1 ? "" : "s"} reported. Facts only — not classified as
        expected or malicious.
      </p>
    </div>
  );
}
