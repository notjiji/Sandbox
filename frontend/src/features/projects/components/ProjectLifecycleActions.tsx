import { Archive, Pencil, RotateCcw, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import FormAlert from "@/shared/components/FormAlert";
import { useConfirm } from "@/shared/hooks/useConfirm";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";
import type { ProjectSummary } from "@/shared/types/project";
import { projectsApi } from "../api";

interface ProjectLifecycleActionsProps {
  project: ProjectSummary;
  onChanged?: () => void;
  compact?: boolean;
}

export default function ProjectLifecycleActions({
  project,
  onChanged,
  compact = false,
}: ProjectLifecycleActionsProps) {
  const navigate = useNavigate();
  const { confirm } = useConfirm();
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async (action: string, fn: () => Promise<void>) => {
    setLoading(action);
    setError(null);
    try {
      await fn();
      onChanged?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed.");
    } finally {
      setLoading(null);
    }
  };

  const confirmDelete = async () => {
    const confirmed = await confirm({
      title: "Delete project",
      description: `Delete "${project.name}"? This archives the project and hides it from active lists.`,
      confirmLabel: "Delete project",
      destructive: true,
    });
    if (!confirmed) return;
    void run("delete", async () => {
      await projectsApi.delete(project.id);
      toast.success("Project deleted.");
      navigate("/projects");
    });
  };

  const confirmArchive = async () => {
    const confirmed = await confirm({
      title: "Archive project",
      description: `Archive "${project.name}"? You can restore it later.`,
      confirmLabel: "Archive project",
      destructive: true,
    });
    if (!confirmed) return;
    void run("archive", async () => {
      await projectsApi.archive(project.id);
      toast.success("Project archived.");
      navigate("/projects");
    });
  };

  return (
    <div className="space-y-3">
      {error && <FormAlert message={error} />}
      <div className={`flex flex-wrap gap-2 ${compact ? "" : ""}`}>
        <Link
          to={`/projects/${project.id}/settings`}
          className="btn-ghost inline-flex items-center gap-2 text-sm"
        >
          <Pencil size={16} />
          Edit
        </Link>

        {project.is_active ? (
          <button
            type="button"
            disabled={loading !== null}
            onClick={() => void confirmArchive()}
            className="btn-ghost inline-flex items-center gap-2 text-sm"
          >
            <Archive size={16} />
            {loading === "archive" ? "Archiving..." : "Archive"}
          </button>
        ) : (
          <button
            type="button"
            disabled={loading !== null}
            onClick={() =>
              run("restore", async () => {
                await projectsApi.restore(project.id);
              })
            }
            className="btn-ghost inline-flex items-center gap-2 text-sm"
          >
            <RotateCcw size={16} />
            {loading === "restore" ? "Restoring..." : "Restore"}
          </button>
        )}

        <button
          type="button"
          disabled={loading !== null}
          onClick={() => void confirmDelete()}
          className="btn-ghost inline-flex items-center gap-2 text-sm text-rose-300 hover:text-rose-200"
        >
          <Trash2 size={16} />
          {loading === "delete" ? "Deleting..." : "Delete"}
        </button>
      </div>
    </div>
  );
}
