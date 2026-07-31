import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { FolderPlus, FolderKanban } from "lucide-react";
import DashboardShell from "../components/DashboardShell";
import FormAlert from "../components/FormAlert";
import FormError from "../components/FormError";
import { projectApi, ApiError } from "../lib/api";

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [form, setForm] = useState({ name: "", description: "" });
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const loadProjects = async () => {
    const response = await projectApi.list();
    setProjects(response?.data?.items ?? []);
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

    load();
    return () => {
      active = false;
    };
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setErrors({ name: "Project name is required" });
      return;
    }

    setCreating(true);
    setAlert("");
    setSuccess("");
    try {
      await projectApi.create({
        name: form.name.trim(),
        description: form.description.trim() || null,
      });
      setSuccess("Project created.");
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
      {success && <FormAlert message={success} variant="success" />}

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6">
          <h2 className="mb-4 text-lg font-semibold text-brand-100">All projects</h2>
          {loading ? (
            <p className="text-brand-500">Loading...</p>
          ) : projects.length === 0 ? (
            <p className="text-brand-500">No projects yet.</p>
          ) : (
            <ul className="space-y-3">
              {projects.map((project) => (
                <li key={project.id}>
                  <div className="flex items-center justify-between rounded-lg border border-brand-800/50 px-4 py-3">
                    <div>
                      <p className="font-medium text-brand-100">{project.name}</p>
                      <p className="text-sm text-brand-500">{project.slug}</p>
                      {project.description && (
                        <p className="mt-1 text-sm text-brand-600">{project.description}</p>
                      )}
                    </div>
                    <FolderKanban size={18} className="text-brand-400" />
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
          <h2 className="text-lg font-semibold text-brand-100">Create project</h2>
          <div>
            <label htmlFor="name" className="terminal-text mb-2 block">name</label>
            <input id="name" name="name" value={form.name} onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))} className="input-field" />
            <FormError message={errors.name} />
          </div>
          <div>
            <label htmlFor="description" className="terminal-text mb-2 block">description</label>
            <textarea id="description" name="description" rows={3} value={form.description} onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))} className="input-field" />
          </div>
          <button type="submit" disabled={creating} className="btn-primary inline-flex w-full items-center justify-center gap-2">
            <FolderPlus size={18} />
            {creating ? "Creating..." : "Create project"}
          </button>
          <p className="text-xs text-brand-600">
            Need assets or scans? They live under each project in the API at{" "}
            <code>/projects/:id/assets</code>.
          </p>
          <Link to="/dashboard" className="link-glow text-sm">
            Back to dashboard
          </Link>
        </motion.form>
      </div>
    </DashboardShell>
  );
}
