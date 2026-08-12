import type { DockerCheck } from "@/shared/types/monitoring";
import { checkLabel } from "../utils";

interface DockerPanelProps {
  docker?: DockerCheck | null;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-brand-800/40 py-3 last:border-b-0">
      <p className="text-sm text-brand-400">{label}</p>
      <p className="text-right text-sm text-brand-100">{value}</p>
    </div>
  );
}

export default function DockerPanel({ docker }: DockerPanelProps) {
  if (!docker) {
    return <p className="text-sm text-brand-600">Docker status will appear after the first heartbeat.</p>;
  }

  if (docker.installed === false) {
    return <p className="text-sm text-brand-600">Docker is not installed on this host.</p>;
  }

  const engine = checkLabel(docker.running, "Running", "Stopped");
  const containers =
    docker.containers != null
      ? String(docker.containers)
      : docker.containers_running != null || docker.containers_stopped != null
        ? String((docker.containers_running ?? 0) + (docker.containers_stopped ?? 0))
        : "—";

  return (
    <div>
      <Row label="Engine" value={engine} />
      <Row label="Version" value={docker.version || "—"} />
      <Row label="Containers" value={containers} />
      <Row
        label="Running"
        value={docker.containers_running != null ? String(docker.containers_running) : "—"}
      />
      <Row
        label="Stopped"
        value={docker.containers_stopped != null ? String(docker.containers_stopped) : "—"}
      />
      <Row label="Images" value={docker.images != null ? String(docker.images) : "—"} />

      {(docker.container_list ?? []).length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wider text-brand-500">
              <tr>
                <th className="pb-2">Container</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Image</th>
              </tr>
            </thead>
            <tbody>
              {(docker.container_list ?? []).slice(0, 20).map((container) => (
                <tr key={container.name} className="border-t border-brand-800/40">
                  <td className="py-2 font-mono text-brand-100">{container.name || "—"}</td>
                  <td className="py-2 text-brand-300">{container.status || "—"}</td>
                  <td className="max-w-[12rem] truncate py-2 text-brand-400">{container.image || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
