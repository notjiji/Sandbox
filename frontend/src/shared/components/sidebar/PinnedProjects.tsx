import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Pin } from "lucide-react";
import { orgStorage } from "@/features/organizations/storage";
import { projectStorage } from "@/features/projects/storage";
import { projectsApi } from "@/features/projects/api";
import type { ProjectSummary } from "@/shared/types/project";
import { cn } from "@/shared/lib/utils";

interface PinnedProjectsProps {
  collapsed?: boolean;
  onNavigate?: () => void;
}

export default function PinnedProjects({ collapsed = false, onNavigate }: PinnedProjectsProps) {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const orgId = orgStorage.getActiveOrgId();

  useEffect(() => {
    if (!orgId) {
      setProjects([]);
      return undefined;
    }

    let active = true;

    async function load() {
      try {
        const pinnedIds = projectStorage.getPinnedProjectIds(orgId!);
        if (!pinnedIds.length) {
          if (active) setProjects([]);
          return;
        }
        const response = await projectsApi.list(true);
        const items = (response?.items ?? []).filter((project) => pinnedIds.includes(project.id));
        const ordered = pinnedIds
          .map((id) => items.find((project) => project.id === id))
          .filter((project): project is ProjectSummary => Boolean(project));
        if (active) setProjects(ordered);
      } catch {
        if (active) setProjects([]);
      }
    }

    void load();

    function handleStorage(event: StorageEvent) {
      if (event.key === "sandbox_pinned_projects") void load();
    }

    window.addEventListener("storage", handleStorage);
    window.addEventListener("pinned-projects-changed", load);
    return () => {
      active = false;
      window.removeEventListener("storage", handleStorage);
      window.removeEventListener("pinned-projects-changed", load);
    };
  }, [orgId]);

  if (projects.length === 0) return null;

  if (collapsed) {
    return (
      <div className="space-y-1 px-2 py-2">
        {projects.slice(0, 3).map((project) => (
          <Link
            key={project.id}
            to={`/projects/${project.id}`}
            onClick={onNavigate}
            title={project.name}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-brand-800/50 text-brand-400 transition hover:border-brand-500/40 hover:text-brand-200"
          >
            <Pin size={14} />
          </Link>
        ))}
      </div>
    );
  }

  return (
    <div className="border-b border-brand-800/40 px-3 py-3">
      <p className="mb-2 px-1 text-[10px] font-medium uppercase tracking-wider text-brand-600">
        Favorites
      </p>
      <ul className="space-y-1">
        {projects.map((project) => (
          <li key={project.id}>
            <Link
              to={`/projects/${project.id}`}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-2 rounded-lg px-2 py-2 text-sm text-brand-300 transition",
                "hover:bg-brand-900/30 hover:text-brand-100",
              )}
            >
              <Pin size={14} className="shrink-0 text-brand-400" />
              <span className="truncate">{project.name}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Star/pin toggle for project list rows. */
export function ProjectPinButton({
  projectId,
  organizationId,
  pinned,
  onToggle,
}: {
  projectId: string;
  organizationId: string;
  pinned: boolean;
  onToggle?: (pinned: boolean) => void;
}) {
  const Icon = Pin;

  return (
    <button
      type="button"
      aria-label={pinned ? "Unpin project" : "Pin project"}
      title={pinned ? "Remove from favorites" : "Pin to favorites"}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        const next = projectStorage.togglePinned(organizationId, projectId);
        window.dispatchEvent(new Event("pinned-projects-changed"));
        onToggle?.(next);
      }}
      className={cn(
        "rounded-md p-1.5 transition",
        pinned
          ? "text-brand-200 hover:bg-brand-900/40"
          : "text-brand-600 hover:bg-brand-900/30 hover:text-brand-300",
      )}
    >
      <Icon size={16} className={pinned ? "fill-brand-400/30" : undefined} />
    </button>
  );
}
