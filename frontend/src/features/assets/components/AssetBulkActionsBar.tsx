import {
  Archive,
  Download,
  Radar,
  Tag,
  Trash2,
  UserPen,
  X,
} from "lucide-react";
import { useState } from "react";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";
import type { AssetBulkAction, AssetBulkActionResponse } from "@/shared/types/asset";
import type { ScanType } from "@/shared/types/scan";
import { assetsApi } from "../api";

interface AssetBulkActionsBarProps {
  projectId: string;
  selectedIds: string[];
  onClear: () => void;
  onComplete: () => void;
}

export default function AssetBulkActionsBar({
  projectId,
  selectedIds,
  onClear,
  onComplete,
}: AssetBulkActionsBarProps) {
  const [busy, setBusy] = useState<AssetBulkAction | null>(null);

  const runAction = async (
    action: AssetBulkAction,
    extras: Partial<{
      tags: string[];
      tag_mode: "add" | "replace";
      owner: string;
      scan_type: ScanType;
    }> = {},
  ) => {
    setBusy(action);
    try {
      const response = await assetsApi.bulk(projectId, {
        asset_ids: selectedIds,
        action,
        ...extras,
      });
      handleResponse(action, response);
      onComplete();
      onClear();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Bulk action failed.");
    } finally {
      setBusy(null);
    }
  };

  const handleResponse = (action: AssetBulkAction, response: AssetBulkActionResponse | null) => {
    if (!response) return;
    if (response.failed > 0) {
      toast.error(`${response.succeeded} succeeded, ${response.failed} failed.`);
    } else {
      toast.success(`${response.succeeded} asset${response.succeeded === 1 ? "" : "s"} updated.`);
    }

    if (action === "export" && response.export_items.length > 0) {
      const blob = new Blob([JSON.stringify(response.export_items, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `assets-export-${new Date().toISOString().slice(0, 10)}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
    }
  };

  const promptTags = () => {
    const value = window.prompt("Tags to assign (comma-separated)");
    if (!value?.trim()) return;
    const tags = value
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
    if (tags.length === 0) return;
    void runAction("assign_tags", { tags, tag_mode: "add" });
  };

  const promptOwner = () => {
    const owner = window.prompt("New owner");
    if (!owner?.trim()) return;
    void runAction("change_owner", { owner: owner.trim() });
  };

  const confirmDelete = () => {
    if (!window.confirm(`Delete ${selectedIds.length} selected asset(s)?`)) return;
    void runAction("delete");
  };

  const confirmArchive = () => {
    if (!window.confirm(`Archive ${selectedIds.length} selected asset(s)?`)) return;
    void runAction("archive");
  };

  if (selectedIds.length === 0) return null;

  return (
    <div className="glass-panel flex flex-col gap-3 border-brand-500/30 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <p className="text-sm text-brand-200">
          <span className="font-semibold text-brand-50">{selectedIds.length}</span> selected
        </p>
        <button
          type="button"
          onClick={onClear}
          className="inline-flex items-center gap-1 text-xs text-brand-500 hover:text-brand-300"
        >
          <X size={14} />
          Clear
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy !== null}
          onClick={confirmArchive}
          className="btn-ghost inline-flex items-center gap-2 text-sm"
        >
          <Archive size={14} />
          {busy === "archive" ? "Archiving..." : "Archive"}
        </button>
        <button
          type="button"
          disabled={busy !== null}
          onClick={confirmDelete}
          className="btn-ghost inline-flex items-center gap-2 text-sm text-red-300 hover:text-red-200"
        >
          <Trash2 size={14} />
          {busy === "delete" ? "Deleting..." : "Delete"}
        </button>
        <button
          type="button"
          disabled={busy !== null}
          onClick={promptTags}
          className="btn-ghost inline-flex items-center gap-2 text-sm"
        >
          <Tag size={14} />
          {busy === "assign_tags" ? "Assigning..." : "Assign tags"}
        </button>
        <button
          type="button"
          disabled={busy !== null}
          onClick={promptOwner}
          className="btn-ghost inline-flex items-center gap-2 text-sm"
        >
          <UserPen size={14} />
          {busy === "change_owner" ? "Updating..." : "Change owner"}
        </button>
        <button
          type="button"
          disabled={busy !== null}
          onClick={() => void runAction("launch_scan", { scan_type: "quick" })}
          className="btn-ghost inline-flex items-center gap-2 text-sm"
        >
          <Radar size={14} />
          {busy === "launch_scan" ? "Launching..." : "Launch scan"}
        </button>
        <button
          type="button"
          disabled={busy !== null}
          onClick={() => void runAction("export")}
          className="btn-ghost inline-flex items-center gap-2 text-sm"
        >
          <Download size={14} />
          {busy === "export" ? "Exporting..." : "Export"}
        </button>
      </div>
    </div>
  );
}
