import type { UpdatesCheck } from "@/shared/types/monitoring";

interface UpdatesPanelProps {
  updates?: UpdatesCheck | null;
}

function Row({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-brand-800/40 py-3 last:border-b-0">
      <p className="text-sm text-brand-400">{label}</p>
      <p className={`text-right text-sm tabular-nums ${warn ? "text-amber-300" : "text-brand-100"}`}>
        {value}
      </p>
    </div>
  );
}

export default function UpdatesPanel({ updates }: UpdatesPanelProps) {
  if (!updates) {
    return (
      <p className="text-sm text-brand-600">
        System update counts will appear after the first heartbeat. The agent only reports availability —
        it never installs packages.
      </p>
    );
  }

  const security = updates.security ?? 0;
  const available = updates.available ?? 0;

  return (
    <div>
      <Row label="Available" value={updates.available != null ? String(updates.available) : "—"} />
      <Row
        label="Security updates"
        value={updates.security != null ? String(updates.security) : "—"}
        warn={security > 0}
      />
      <Row label="Package manager" value={updates.manager || "—"} />
      <Row
        label="Reboot required"
        value={
          updates.reboot_required == null ? "—" : updates.reboot_required ? "Yes" : "No"
        }
        warn={updates.reboot_required === true}
      />
      {security > 0 && (
        <p className="mt-3 text-xs text-amber-300/90">
          {security} security update{security === 1 ? "" : "s"} pending → MEDIUM risk finding
          {available > security ? ` (${available} total available)` : ""}.
        </p>
      )}
    </div>
  );
}
