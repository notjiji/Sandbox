import type { SshCheck } from "@/shared/types/monitoring";
import { checkLabel } from "../utils";

interface SshPanelProps {
  ssh?: SshCheck | null;
}

function Row({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-brand-800/40 py-3 last:border-b-0">
      <p className="text-sm text-brand-400">{label}</p>
      <p className={`text-right text-sm ${warn ? "text-amber-300" : "text-brand-100"}`}>{value}</p>
    </div>
  );
}

function rawOrLabel(
  enabled: boolean | null | undefined,
  raw: string | null | undefined,
  yesLabel: string,
  noLabel: string,
): string {
  if (raw) return raw;
  return checkLabel(enabled, yesLabel, noLabel);
}

export default function SshPanel({ ssh }: SshPanelProps) {
  if (!ssh) {
    return (
      <p className="text-sm text-brand-600">
        SSH configuration will appear after the first heartbeat. Assessment is read-only — the agent never
        changes sshd settings.
      </p>
    );
  }

  return (
    <div>
      <Row
        label="Root login"
        value={rawOrLabel(ssh.permit_root_login, ssh.permit_root_login_raw, "yes", "no")}
        warn={ssh.permit_root_login === true}
      />
      <Row
        label="Password authentication"
        value={rawOrLabel(
          ssh.password_authentication,
          ssh.password_authentication_raw,
          "yes",
          "no",
        )}
        warn={ssh.password_authentication === true}
      />
      <Row
        label="Public key authentication"
        value={rawOrLabel(ssh.pubkey_authentication, ssh.pubkey_authentication_raw, "yes", "no")}
        warn={ssh.pubkey_authentication === false}
      />
      <Row label="SSH port" value={ssh.port != null ? String(ssh.port) : "—"} />
      <Row label="Protocol" value={ssh.protocol || "—"} warn={Boolean(ssh.protocol?.includes("1"))} />
      <p className="mt-3 text-xs text-brand-600">
        Source: {ssh.config_source || "unknown"} · read-only assessment
      </p>
    </div>
  );
}
