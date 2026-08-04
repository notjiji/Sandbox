import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { FilePlus, FileText, Sparkles, Trash2 } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import { organizationsApi } from "@/features/organizations/api";
import FormError from "@/shared/components/FormError";
import EmptyState from "@/shared/components/EmptyState";
import ListSearchBar from "@/shared/components/ListSearchBar";
import OrganizationLogo from "@/shared/components/OrganizationLogo";
import { ListSkeleton } from "@/shared/components/ui/Skeleton";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";import type { ValidationErrors } from "@/shared/types/api";
import type { ProjectSummary } from "@/shared/types/project";
import type { ReportStatus } from "@/shared/types/report";
import type { OrganizationDetail } from "@/shared/types/organization";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import { reportsApi } from "../api";

interface ReportItem {
  id: string;
  name: string;
  description?: string | null;
  status: ReportStatus | string;
}

interface CreateReportForm {
  name: string;
  description: string;
}

interface CreateReportPayload {
  name: string;
  description?: string | null;
}

export default function Reports() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [organization, setOrganization] = useState<OrganizationDetail | null>(null);
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [form, setForm] = useState<CreateReportForm>({ name: "", description: "" });
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);  const [creating, setCreating] = useState(false);
  const [actionId, setActionId] = useState<string | null>(null);

  const loadData = async () => {
    if (!projectId) return;
    const [projectResponse, reportsResponse, orgResponse] = await Promise.all([
      projectsApi.get(projectId),
      reportsApi.list(projectId),
      organizationsApi.getCurrent(),
    ]);
    setProject(projectResponse ?? null);
    setOrganization(orgResponse ?? null);
    setReports((reportsResponse?.items ?? []) as unknown as ReportItem[]);
  };

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        await loadData();
      } catch (error) {
        if (active) {
          toast.error(error instanceof ApiError ? error.message : "Unable to load reports.");
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

  const filteredReports = useMemo(() => {
    return reports.filter((report) => {
      if (statusFilter && report.status !== statusFilter) return false;
      if (!search.trim()) return true;
      const needle = search.toLowerCase();
      return (
        report.name.toLowerCase().includes(needle) ||
        (report.description?.toLowerCase().includes(needle) ?? false)
      );
    });
  }, [reports, search, statusFilter]);

  const handleCreate = async (e: React.FormEvent) => {    e.preventDefault();
    if (!projectId) return;
    if (!form.name.trim()) {
      setErrors({ name: "Report name is required" });
      return;
    }

    setCreating(true);
    setErrors({});
    try {
      const payload: CreateReportPayload = {
        name: form.name.trim(),
        description: form.description.trim() || null,
      };
      await reportsApi.create(
        projectId,
        payload as unknown as Parameters<typeof reportsApi.create>[1],
      );
      toast.success("Report created.");
      setForm({ name: "", description: "" });
      await loadData();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to create report.");
    } finally {      setCreating(false);
    }
  };

  const handleGenerate = async (reportId: string) => {
    if (!projectId) return;
    setActionId(reportId);
    try {
      await reportsApi.generate(projectId, reportId);
      toast.success("Report generation started.");
      await loadData();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to generate report.");
    } finally {      setActionId(null);
    }
  };

  const handleDelete = async (reportId: string) => {
    if (!projectId) return;
    setActionId(reportId);
    try {
      await reportsApi.delete(projectId, reportId);
      toast.success("Report deleted.");
      await loadData();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to delete report.");
    } finally {      setActionId(null);
    }
  };

  return (
    <DashboardShell title="Reports" subtitle="Generate and manage project reports.">
      <ProjectNav projectName={project?.name} active="reports" />
      {organization && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 flex items-center gap-3 rounded-xl border border-brand-800/50 bg-void-200/20 px-4 py-3"
        >
          <OrganizationLogo
            name={organization.name}
            logoUrl={organization.logo_url}
            size="md"
          />
          <div>
            <p className="text-sm font-medium text-brand-100">{organization.name}</p>
            <p className="text-xs text-brand-500">Reports are branded with your organization logo</p>
          </div>
        </motion.div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-6"
        >
          <h2 className="mb-4 text-lg font-semibold text-brand-100">All reports</h2>
          <div className="mb-4 grid gap-3 sm:grid-cols-[1fr_12rem]">
            <ListSearchBar value={search} onChange={setSearch} placeholder="Search reports..." />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field"
              aria-label="Filter by status"
            >
              <option value="">All statuses</option>
              <option value="draft">Draft</option>
              <option value="generating">Generating</option>
              <option value="ready">Ready</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          {loading ? (
            <ListSkeleton rows={4} />
          ) : filteredReports.length === 0 ? (
            <EmptyState
              compact
              icon={FileText}
              title={search || statusFilter ? "No matching reports" : "No reports yet"}
              description={
                search || statusFilter
                  ? "Adjust your search or status filter."
                  : "Create a report to generate branded output for this project."
              }
            />
          ) : (
            <ul className="space-y-3">
              {filteredReports.map((report) => (                <li
                  key={report.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-brand-800/50 px-4 py-3"
                >
                  <div>
                    <p className="font-medium text-brand-100">{report.name}</p>
                    {report.description && (
                      <p className="mt-1 text-sm text-brand-500">{report.description}</p>
                    )}
                    <p className="mt-1 text-xs uppercase tracking-wide text-brand-600">
                      {report.status}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText size={18} className="text-brand-400" />
                    <button
                      type="button"
                      disabled={actionId === report.id}
                      onClick={() => handleGenerate(report.id)}
                      className="btn-primary inline-flex items-center gap-1 text-sm"
                    >
                      <Sparkles size={14} />
                      Generate
                    </button>
                    <button
                      type="button"
                      disabled={actionId === report.id}
                      onClick={() => handleDelete(report.id)}
                      className="btn-ghost inline-flex items-center gap-1 text-sm"
                    >
                      <Trash2 size={14} />
                      Delete
                    </button>
                  </div>
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
          <h2 className="text-lg font-semibold text-brand-100">Create report</h2>
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
            <FilePlus size={18} />
            {creating ? "Creating..." : "Create report"}
          </button>
        </motion.form>
      </div>
    </DashboardShell>
  );
}
