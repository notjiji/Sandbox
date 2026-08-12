import type { FirewallCheck } from "@/shared/types/monitoring";
import { checkLabel } from "../utils";

interface FirewallPanelProps {
  firewall?: FirewallCheck | null;
}

function Row({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-brand-800/40 py-3 last:border-b-0">
      <p className="text-sm text-brand-400">{label}</p>
      <p className={`text-right text-sm ${warn ? "text-amber-300" : "text-brand-100"}`}>{value}</p>
    </div>
  );
}

export default function FirewallPanel({ firewall }: FirewallPanelProps) {
  if (!firewall) {
    return (
      <p className="text-sm text-brand-600">
        No firewall mechanism reported (UFW, firewalld, nftables, or iptables). Read-only assessment only —
        the platform never changes firewall rules.
      </p>
    );
  }

  const status = checkLabel(firewall.enabled, "ENABLED", "DISABLED");
  const backend = firewall.backend ? firewall.backend.toUpperCase() : "UNKNOWN";

  return (
    <div>
      <Row label="Mechanism" value={backend} />
      <Row label="Status" value={status} warn={firewall.enabled === false} />
      <Row label="Default incoming" value={firewall.default_incoming || "—"} />
      <Row label="Default outgoing" value={firewall.default_outgoing || "—"} />
      <p className="mt-3 text-xs text-brand-600">Read-only assessment. Firewall rules are never modified.</p>
    </div>
  );
}
