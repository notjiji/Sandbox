import { Link } from "react-router-dom";
import { Globe, Plus } from "lucide-react";
import EmptyState from "@/shared/components/EmptyState";

interface AssetEmptyStateProps {
  projectId: string;
  filtered?: boolean;
  compact?: boolean;
}

export default function AssetEmptyState({
  projectId,
  filtered = false,
  compact = false,
}: AssetEmptyStateProps) {
  if (filtered) {
    return (
      <EmptyState
        compact={compact}
        icon={Globe}
        title="No matching assets"
        description="Try adjusting your search, tags, or filters to find what you're looking for."
      />
    );
  }

  return (
    <EmptyState
      compact={compact}
      icon={Globe}
      title="No assets yet"
      description={
        <span>
          Add your first{" "}
          <span className="text-brand-400">website</span>,{" "}
          <span className="text-brand-400">domain</span>, or{" "}
          <span className="text-brand-400">server</span> to begin monitoring.
        </span>
      }
      action={
        <Link
          to={`/projects/${projectId}/assets/new`}
          className="btn-primary inline-flex items-center gap-2"
        >
          <Plus size={16} />
          Add your first asset
        </Link>
      }
    />
  );
}
