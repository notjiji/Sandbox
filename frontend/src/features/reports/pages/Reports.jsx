import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { FilePlus, FileText, Sparkles, Trash2 } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError } from "@/shared/api/client";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import { reportsApi } from "../api";

export default function Reports() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [reports, setReports] = useState([]);
  const [form, setForm] = useState({ name: "", description: "" });
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [actionId, setActionId] = useState(null);

  const loadData = async () => {
    const [projectResponse, reportsResponse] = await Promise.all([
      projectsApi.get(projectId),
      reportsApi.list(projectId),
    ]);
    setProject(projectResponse?.data ?? null);
    setReports(reportsResponse?.data?.items ?? []);
  };

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        await loadData();
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load reports.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [projectId]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setErrors({ name: "Report name is required" });
      return;
    }

    setCreating(true);
    setAlert("");
    setSuccess("");
    setErrors({});
    try {
      await reportsApi.create(projectId, {
        name: form.name.trim(),
        description: form.description.trim() || null,
      });
      setSuccess("Report created.");
      setForm({ name: "", description: "" });
      await loadData();
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to create report.");
    } finally {
      setCreating(false);
    }
  };

  const handleGenerate = async (reportId) => {
    setActionId(reportId);
    setAlert("");
    setSuccess("");
    try {
      await reportsApi.generate(projectId, reportId);
      setSuccess("Report generation started.");
      await loadData();
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to generate report.");
    } finally {
      setActionId(null);
    }
  };

  const handleDelete = async (reportId) => {
    setActionId(reportId);
    setAlert("");
    setSuccess("");
    try {
      await reportsApi.delete(projectId, reportId);
      setSuccess("Report deleted.");
      await loadData();
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to delete report.");
    } finally {
      setActionId(null);
    }
  };

  return (
    <DashboardShell title="Reports" subtitle="Generate and manage project reports.">
      {alert && <FormAlert message={alert} />}
      {success && <FormAlert message={success} variant="success" />}
      <ProjectNav projectName={project?.name} active="reports" />

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6">
          <h2 className="mb-4 text-lg font-semibold text-brand-100">All reports</h2>
          {loading ? (
            <p className="text-brand-500">Loading...</p>
          ) : reports.length === 0 ? (
            <p className="text-brand-500">No reports yet.</p>
          ) : (
            <ul className="space-y-3">
              {reports.map((report) => (
                <li
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
