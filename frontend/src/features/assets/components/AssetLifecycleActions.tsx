import { Archive, RotateCcw, Trash2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { AssetSummary } from "@/shared/types/asset";
import { assetsApi } from "../api";

type LifecycleAction = "archive" | "restore" | "delete";

interface AssetLifecycleActionsProps {
  projectId: string;
  asset: AssetSummary;
  onChanged?: () => void;
}

export default function AssetLifecycleActions({
  projectId,
  asset,
  onChanged,
}: AssetLifecycleActionsProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState<LifecycleAction | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async (action: LifecycleAction, label: string) => {
    setLoading(action);
    setError(null);
    try {
      if (action === "archive") await assetsApi.archive(projectId, asset.id);
      if (action === "restore") await assetsApi.restore(projectId, asset.id);
      if (action === "delete") {
        await assetsApi.delete(projectId, asset.id);
        navigate(`/projects/${projectId}/assets`);
        return;
      }
      onChanged?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : `Unable to ${label} asset.`);
    } finally {
      setLoading(null);
    }
  };

  const confirmDelete = () => {
    if (
      window.confirm(
        `Delete "${asset.name}"? This soft-deletes the asset and preserves scan history.`,
      )
    ) {
      void run("delete", "delete");
    }
  };

  return (
    <div className="space-y-3">
      {error && <FormAlert message={error} />}
      <div className="flex flex-wrap gap-2">
        {asset.status !== "archived" && asset.status !== "deleted" && (
          <button
            type="button"
            disabled={loading !== null}
            onClick={() => run("archive", "archive")}
            className="btn-ghost inline-flex items-center gap-2 text-sm"
          >
            <Archive size={16} />
            {loading === "archive" ? "Archiving..." : "Archive"}
          </button>
        )}
        {(asset.status === "archived" || asset.status === "deleted") && (
          <button
            type="button"
            disabled={loading !== null}
            onClick={() => run("restore", "restore")}
            className="btn-ghost inline-flex items-center gap-2 text-sm"
          >
            <RotateCcw size={16} />
            {loading === "restore" ? "Restoring..." : "Restore"}
          </button>
        )}
        {asset.status !== "deleted" && (
          <button
            type="button"
            disabled={loading !== null}
            onClick={confirmDelete}
            className="btn-ghost inline-flex items-center gap-2 text-sm text-red-400 hover:text-red-300"
          >
            <Trash2 size={16} />
            {loading === "delete" ? "Deleting..." : "Delete"}
          </button>
        )}
      </div>
    </div>
  );
}
