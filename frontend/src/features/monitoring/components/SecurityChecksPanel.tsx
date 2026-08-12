import type { SecurityPayload } from "@/shared/types/monitoring";
import { checkLabel } from "../utils";

interface SecurityChecksPanelProps {
  security?: SecurityPayload | null;
}

function Row({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-brand-800/40 py-3 last:border-b-0">
      <p className="text-sm text-brand-400">{label}</p>
      <p className={`text-right text-sm ${warn ? "text-amber-300" : "text-brand-100"}`}>{value}</p>
    </div>
  );
}

export default function SecurityChecksPanel({ security }: SecurityChecksPanelProps) {
  if (!security) {
    return <p className="text-sm text-brand-600">Security checks will appear after the first heartbeat.</p>;
  }

  const firewall = security.firewall;
  const ssh = security.ssh;
  const fail2ban = security.fail2ban;
  const updates = security.updates;
  const system = security.system;

  const firewallSummary = firewall
    ? [
        checkLabel(firewall.enabled, "ENABLED", "DISABLED"),
        firewall.backend ? firewall.backend.toUpperCase() : null,
        firewall.default_incoming ? `in ${firewall.default_incoming}` : null,
        firewall.default_outgoing ? `out ${firewall.default_outgoing}` : null,
      ]
        .filter(Boolean)
        .join(" · ")
    : "Not reported";

  return (
    <div>
      <Row label="Firewall" value={firewallSummary} warn={firewall?.enabled === false} />
      <Row
        label="SSH root login"
        value={ssh ? checkLabel(ssh.permit_root_login, "Enabled", "Disabled") : "Not reported"}
        warn={ssh?.permit_root_login === true}
      />
      <Row
        label="SSH password auth"
        value={ssh ? checkLabel(ssh.password_authentication, "Enabled", "Disabled") : "Not reported"}
        warn={ssh?.password_authentication === true}
      />
      <Row
        label="Fail2Ban"
        value={
          fail2ban
            ? `${checkLabel(fail2ban.enabled, "Running", "Inactive")}${
                fail2ban.jails?.length ? ` · ${fail2ban.jails.length} jail(s)` : ""
              }`
            : "Not reported"
        }
        warn={fail2ban?.enabled === false}
      />
      <Row
        label="Updates"
        value={
          updates
            ? `${updates.available ?? 0} available (${updates.security ?? 0} security)`
            : "Not reported"
        }
        warn={(updates?.security ?? 0) > 0}
      />
      <Row label="OS" value={system?.os || "Not reported"} />
      <Row label="Hostname" value={system?.hostname || "Not reported"} />
    </div>
  );
}
