import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Database, FileText, Globe, Save, Settings, Users } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import Pagination from "@/shared/components/Pagination";
import { ApiError } from "@/shared/api/client";
import type { ValidationErrors } from "@/shared/types/api";
import type { ProjectSummary } from "@/shared/types/project";
import type { AuditLogSummary } from "@/shared/types/organization-overview";
import {
  formatActionLabel,
  formatRelativeTime,
} from "@/features/organizations/utils/format";
import { projectsApi } from "../api";
import ProjectLifecycleActions from "../components/ProjectLifecycleActions";
import ProjectNav from "../components/ProjectNav";

const TABS = [
  { key: "general", label: "General", icon: Settings },
  { key: "members", label: "Members", icon: Users },
  { key: "assets", label: "Assets", icon: Globe },
  { key: "reports", label: "Reports", icon: FileText },
  { key: "activity", label: "Activity", icon: Database },
] as const;

type SettingsTab = (typeof TABS)[number]["key"];

interface GeneralForm {
  name: string;
  description: string;
}

export default function ProjectSettings() {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = (searchParams.get("tab") as SettingsTab) || "general";

  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [form, setForm] = useState<GeneralForm>({ name: "", description: "" });
  const [activity, setActivity] = useState<AuditLogSummary[]>([]);
  const [activityTotal, setActivityTotal] = useState(0);
  const [activityPage, setActivityPage] = useState(1);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const setTab = (next: SettingsTab) => {
    setSearchParams({ tab: next });
  };

  const loadProject = async () => {
    if (!projectId) return;
    const data = await projectsApi.get(projectId);
    setProject(data ?? null);
    setForm({
      name: data?.name ?? "",
      description: data?.description ?? "",
    });
  };

  const loadActivity = async () => {
    if (!projectId) return;
    const data = await projectsApi.getActivity(projectId, activityPage, 20);
    setActivity(data?.items ?? []);
    setActivityTotal(data?.total ?? 0);
  };

  useEffect(() => {
    let active = true;
    if (!projectId) return undefined;

    async function load() {
      try {
        await loadProject();
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load project.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [projectId]);

  useEffect(() => {
    if (tab !== "activity" || !projectId) return undefined;
    let active = true;

    async function load() {
      try {
        await loadActivity();
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load activity.");
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [tab, projectId, activityPage]);

  const handleSave = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!projectId || !form.name.trim()) {
      setErrors({ name: "Project name is required" });
      return;
    }

    setSaving(true);
    setAlert("");
    setSuccess("");
    try {
      const updated = await projectsApi.update(projectId, {
        name: form.name.trim(),
        description: form.description.trim() || undefined,
      });
      setProject(updated ?? null);
      setSuccess("Project settings saved.");
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to save project.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashboardShell
      title={project?.name ?? "Project settings"}
      subtitle="Manage project configuration and lifecycle."
    >
      {alert && <FormAlert message={alert} />}
      {success && <FormAlert message={success} variant="success" />}
      <ProjectNav projectName={project?.name} active="settings" />

      <div className="mb-6 flex flex-wrap gap-2">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition ${
              tab === key
                ? "border-brand-500/50 bg-brand-900/40 text-brand-100"
                : "border-brand-800/50 text-brand-400 hover:border-brand-600/40 hover:text-brand-200"
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-brand-500">Loading settings...</p>
      ) : !project ? (
        <p className="text-brand-500">Project not found.</p>
      ) : (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          {tab === "general" && (
            <div className="grid gap-6 lg:grid-cols-[1fr_18rem]">
              <form onSubmit={handleSave} className="glass-panel space-y-4 p-6">
                <h2 className="text-lg font-semibold text-brand-100">General</h2>
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
                    rows={4}
                    value={form.description}
                    onChange={(e) =>
                      setForm((prev) => ({ ...prev, description: e.target.value }))
                    }
                    className="input-field"
                  />
                </div>
                <p className="text-sm text-brand-600">
                  Slug: <span className="text-brand-400">{project.slug}</span>
                </p>
                <button
                  type="submit"
                  disabled={saving}
                  className="btn-primary inline-flex items-center gap-2"
                >
                  <Save size={16} />
                  {saving ? "Saving..." : "Save changes"}
                </button>
              </form>

              <div className="glass-panel h-fit p-6">
                <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-brand-400">
                  Lifecycle
                </h3>
                <ProjectLifecycleActions
                  project={project}
                  onChanged={() => void loadProject()}
                />
              </div>
            </div>
          )}

          {tab === "members" && (
            <div className="glass-panel p-6">
              <h2 className="text-lg font-semibold text-brand-100">Members</h2>
              <p className="mt-2 text-sm text-brand-500">
                Project access is managed at the organization level. All active organization
                members can access projects based on their role.
              </p>
              <Link to="/organization/members" className="btn-primary mt-4 inline-flex">
                Manage organization members
              </Link>
            </div>
          )}

          {tab === "assets" && (
            <div className="glass-panel p-6">
              <h2 className="text-lg font-semibold text-brand-100">Assets</h2>
              <p className="mt-2 text-sm text-brand-500">
                View and manage assets scoped to this project.
              </p>
              <Link
                to={`/projects/${projectId}/assets`}
                className="btn-primary mt-4 inline-flex"
              >
                Open assets
              </Link>
            </div>
          )}

          {tab === "reports" && (
            <div className="glass-panel p-6">
              <h2 className="text-lg font-semibold text-brand-100">Reports</h2>
              <p className="mt-2 text-sm text-brand-500">
                Generate and download reports for this project.
              </p>
              <Link
                to={`/projects/${projectId}/reports`}
                className="btn-primary mt-4 inline-flex"
              >
                Open reports
              </Link>
            </div>
          )}

          {tab === "activity" && (
            <div className="glass-panel p-6">
              <h2 className="mb-4 text-lg font-semibold text-brand-100">Activity</h2>
              {activity.length === 0 ? (
                <p className="text-sm text-brand-600">No activity recorded for this project.</p>
              ) : (
                <ul className="space-y-3">
                  {activity.map((entry) => (
                    <li
                      key={entry.id}
                      className="flex items-start gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3"
                    >
                      <Database size={14} className="mt-0.5 shrink-0 text-brand-500" />
                      <div>
                        <p className="text-sm text-brand-200">
                          {formatActionLabel(entry.action)}
                        </p>
                        <p className="text-xs text-brand-600">
                          {entry.resource_type ?? "system"} ·{" "}
                          {formatRelativeTime(entry.created_at)}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-6">
                <Pagination
                  page={activityPage}
                  limit={20}
                  total={activityTotal}
                  onPageChange={setActivityPage}
                />
              </div>
            </div>
          )}
        </motion.div>
      )}
    </DashboardShell>
  );
}
