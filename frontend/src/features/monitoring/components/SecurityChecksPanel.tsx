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
      ]
        .filter(Boolean)
        .join(" · ")
    : "Not reported";

  const sshSummary = ssh
    ? [
        ssh.port != null ? `port ${ssh.port}` : null,
        ssh.password_authentication === true
          ? "password on"
          : ssh.password_authentication === false
            ? "password off"
            : null,
        ssh.permit_root_login === true ? "root on" : null,
      ]
        .filter(Boolean)
        .join(" · ") || "Reported"
    : "Not reported";

  const f2bRunning = fail2ban?.running ?? fail2ban?.enabled;
  const fail2banSummary = fail2ban
    ? fail2ban.installed === false
      ? "Not installed"
      : [
          checkLabel(f2bRunning, "ACTIVE", "INACTIVE"),
          `${fail2ban.jail_count ?? fail2ban.jails?.length ?? 0} jail(s)`,
          fail2ban.banned_ips != null ? `${fail2ban.banned_ips} banned` : null,
        ]
          .filter(Boolean)
          .join(" · ")
    : "Not reported";

  return (
    <div>
      <Row label="Firewall" value={firewallSummary} warn={firewall?.enabled === false} />
      <Row
        label="SSH"
        value={sshSummary}
        warn={ssh?.permit_root_login === true || ssh?.password_authentication === true}
      />
      <Row
        label="Fail2Ban"
        value={fail2banSummary}
        warn={fail2ban?.installed === false || f2bRunning === false}
      />
      <Row
        label="Updates"
        value={
          updates
            ? `${updates.available ?? 0} available · ${updates.security ?? 0} security`
            : "Not reported"
        }
        warn={(updates?.security ?? 0) > 0 || updates?.reboot_required === true}
      />
      <Row label="OS" value={system?.os || "Not reported"} />
      <Row label="Hostname" value={system?.hostname || "Not reported"} />
    </div>
  );
}
