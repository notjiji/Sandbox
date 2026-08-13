import type { Fail2BanCheck } from "@/shared/types/monitoring";
import { checkLabel } from "../utils";

interface Fail2BanPanelProps {
  fail2ban?: Fail2BanCheck | null;
}

function Row({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-brand-800/40 py-3 last:border-b-0">
      <p className="text-sm text-brand-400">{label}</p>
      <p className={`text-right text-sm ${warn ? "text-amber-300" : "text-brand-100"}`}>{value}</p>
    </div>
  );
}

export default function Fail2BanPanel({ fail2ban }: Fail2BanPanelProps) {
  if (!fail2ban) {
    return <p className="text-sm text-brand-600">Fail2Ban status will appear after the first heartbeat.</p>;
  }

  const running = fail2ban.running ?? fail2ban.enabled;
  const jailCount = fail2ban.jail_count ?? fail2ban.jails?.length ?? 0;
  const status =
    fail2ban.installed === false
      ? "NOT INSTALLED"
      : checkLabel(running, "ACTIVE", "INACTIVE");

  return (
    <div>
      <Row
        label="Status"
        value={status}
        warn={fail2ban.installed === false || running === false}
      />
      <Row
        label="Installed"
        value={
          fail2ban.installed == null
            ? "—"
            : fail2ban.installed
              ? "Yes"
              : "No"
        }
        warn={fail2ban.installed === false}
      />
      <Row label="Jails" value={String(jailCount)} />
      <Row
        label="Banned IPs"
        value={fail2ban.banned_ips != null ? String(fail2ban.banned_ips) : "—"}
      />
      {(fail2ban.jails ?? []).length > 0 && (
        <p className="mt-3 font-mono text-xs text-brand-500">{fail2ban.jails?.join(", ")}</p>
      )}
    </div>
  );
}
