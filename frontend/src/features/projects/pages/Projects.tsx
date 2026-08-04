import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { FolderPlus, FolderKanban } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import { orgStorage } from "@/features/organizations/storage";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import EmptyState from "@/shared/components/EmptyState";
import ListSearchBar from "@/shared/components/ListSearchBar";
import { ProjectPinButton } from "@/shared/components/sidebar/PinnedProjects";
import { ListSkeleton } from "@/shared/components/ui/Skeleton";
import { toast } from "@/shared/lib/toast";
import { projectStorage } from "../storage";
import { ApiError } from "@/shared/api/client";
import type { ValidationErrors } from "@/shared/types/api";
import type { ProjectSummary } from "@/shared/types/project";
import { projectsApi } from "../api";

interface CreateProjectForm {
  name: string;
  description: string;
}

export default function Projects() {
  const [searchParams] = useSearchParams();
  const orgId = orgStorage.getActiveOrgId() ?? "";
  const [showArchived, setShowArchived] = useState(false);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [pinnedIds, setPinnedIds] = useState<string[]>(() =>
    orgId ? projectStorage.getPinnedProjectIds(orgId) : [],
  );
  const [form, setForm] = useState<CreateProjectForm>({ name: "", description: "" });
  const [search, setSearch] = useState("");
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [alert, setAlert] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const loadProjects = async () => {
    const response = await projectsApi.list(showArchived);
    setProjects(response?.items ?? []);
  };

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        await loadProjects();
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load projects.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [showArchived]);

  useEffect(() => {
    if (searchParams.get("create") === "1") {
      document.getElementById("name")?.focus();
    }
  }, [searchParams]);

  useEffect(() => {
    function syncPinned() {
      if (orgId) setPinnedIds(projectStorage.getPinnedProjectIds(orgId));
    }
    window.addEventListener("pinned-projects-changed", syncPinned);
    return () => window.removeEventListener("pinned-projects-changed", syncPinned);
  }, [orgId]);

  const sortedProjects = [...projects]
    .filter((project) => {
      if (!search.trim()) return true;
      const needle = search.toLowerCase();
      return (
        project.name.toLowerCase().includes(needle) ||
        project.slug.toLowerCase().includes(needle) ||
        (project.description?.toLowerCase().includes(needle) ?? false)
      );
    })
    .sort((a, b) => {
    const aPinned = pinnedIds.includes(a.id);
    const bPinned = pinnedIds.includes(b.id);
    if (aPinned && !bPinned) return -1;
    if (!aPinned && bPinned) return 1;
    return a.name.localeCompare(b.name);
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setErrors({ name: "Project name is required" });
      return;
    }

    setCreating(true);
    setAlert("");
    try {
      await projectsApi.create({
        name: form.name.trim(),
        description: form.description.trim() || undefined,
      });
      toast.success("Project created.");
      setForm({ name: "", description: "" });
      await loadProjects();
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to create project.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <DashboardShell title="Projects" subtitle="Organize assets, scans, and reports by project.">
      {alert && <FormAlert message={alert} />}

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-6"
        >
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-brand-100">All projects</h2>
            <label className="flex items-center gap-2 text-sm text-brand-500">
              <input
                type="checkbox"
                checked={showArchived}
                onChange={(e) => setShowArchived(e.target.checked)}
              />
              Show archived
            </label>
          </div>
          <ListSearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search projects..."
            className="mb-4"
          />
          {loading ? (
            <ListSkeleton rows={4} />
          ) : sortedProjects.length === 0 ? (
            <EmptyState
              icon={FolderKanban}
              title={search ? "No matching projects" : "No projects yet"}
              description={
                search
                  ? "Try a different search term or clear the filter."
                  : "Create your first project to organize assets, scans, and reports."
              }
              action={
                !search ? (
                  <button
                    type="button"
                    className="btn-primary inline-flex items-center gap-2"
                    onClick={() => document.getElementById("name")?.focus()}
                  >
                    <FolderPlus size={16} />
                    Create your first project
                  </button>
                ) : undefined
              }
            />
          ) : (
            <ul className="space-y-3">
              {sortedProjects.map((project) => (
                <li key={project.id}>
                  <Link
                    to={`/projects/${project.id}`}
                    className="flex items-center justify-between rounded-lg border border-brand-800/50 px-4 py-3 transition hover:border-brand-500/40"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-brand-100">
                        {project.name}
                        {pinnedIds.includes(project.id) && (
                          <span className="ml-2 text-xs text-brand-500">Pinned</span>
                        )}
                        {!project.is_active && (
                          <span className="ml-2 rounded-full bg-brand-800/60 px-2 py-0.5 text-xs text-brand-400">
                            Archived
                          </span>
                        )}
                      </p>
                      <p className="text-sm text-brand-500">{project.slug}</p>
                      {project.description && (
                        <p className="mt-1 text-sm text-brand-600">{project.description}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      {orgId && (
                        <ProjectPinButton
                          projectId={project.id}
                          organizationId={orgId}
                          pinned={pinnedIds.includes(project.id)}
                          onToggle={() =>
                            setPinnedIds(projectStorage.getPinnedProjectIds(orgId))
                          }
                        />
                      )}
                      <FolderKanban size={18} className="text-brand-400" />
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </motion.div>

        <motion.form
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleCreate}
          className="glass-panel h-fit space-y-4 p-6"
        >
          <h2 className="text-lg font-semibold text-brand-100">Create project</h2>
          <div>
            <label htmlFor="name" className="terminal-text mb-2 block">
              name
            </label>
            <input
              id="name"
              name="name"
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              className="input-field"
            />
            <FormError message={errors.name} />
          </div>
          <div>
            <label htmlFor="description" className="terminal-text mb-2 block">
              description
            </label>
            <textarea
              id="description"
              name="description"
              rows={3}
              value={form.description}
              onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
              className="input-field"
            />
          </div>
          <button
            type="submit"
            disabled={creating}
            className="btn-primary inline-flex w-full items-center justify-center gap-2"
          >
            <FolderPlus size={18} />
            {creating ? "Creating..." : "Create project"}
          </button>
          <Link to="/dashboard" className="link-glow text-sm">
            Back to dashboard
          </Link>
        </motion.form>
      </div>
    </DashboardShell>
  );
}
