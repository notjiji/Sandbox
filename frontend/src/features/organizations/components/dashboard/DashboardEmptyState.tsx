import { Link } from "react-router-dom";
import { FolderPlus, Radar } from "lucide-react";

interface DashboardEmptyStateProps {
  primaryProjectId: string | null;
  canRunScan: boolean;
}

export default function DashboardEmptyState({
  primaryProjectId,
  canRunScan,
}: DashboardEmptyStateProps) {
  const assetsHref = primaryProjectId
    ? `/projects/${primaryProjectId}/assets/new`
    : "/projects";

  return (
    <div className="glass-panel flex flex-col items-center px-6 py-16 text-center">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-brand-700/50 bg-brand-950/40">
        <Radar size={28} className="text-brand-400" />
      </div>
      <h2 className="text-xl font-semibold text-brand-50">
        Your security dashboard isn&apos;t ready yet
      </h2>
      <p className="mt-3 max-w-md text-sm text-brand-400">
        Add your first asset and run a security scan to begin measuring your
        organization&apos;s security posture.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <Link to={assetsHref} className="btn-primary inline-flex items-center gap-2">
          <FolderPlus size={16} />
          Add Asset
        </Link>
        {canRunScan && primaryProjectId && (
          <Link
            to={`/projects/${primaryProjectId}/assets`}
            className="btn-ghost inline-flex items-center gap-2"
          >
            <Radar size={16} />
            Run First Scan
          </Link>
        )}
      </div>
    </div>
  );
}
