import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Globe, Plus, Server } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError } from "@/shared/api/client";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import { assetsApi } from "../api";
import { useProjectAssets } from "../hooks";
import { ASSET_TYPES } from "../types";

export default function Assets() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const { assets, loading, error, reload } = useProjectAssets(projectId);
  const [form, setForm] = useState({ name: "", identifier: "", type: "host" });
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    let active = true;
    projectsApi.get(projectId).then((response) => {
      if (active) setProject(response?.data ?? null);
    }).catch(() => {});
    return () => {
      active = false;
    };
  }, [projectId]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setErrors({ name: "Asset name is required" });
      return;
    }

    setCreating(true);
    setAlert("");
    setSuccess("");
    setErrors({});
    try {
      await assetsApi.create(projectId, {
        name: form.name.trim(),
        identifier: form.identifier.trim() || null,
        type: form.type,
      });
      setSuccess("Asset created.");
      setForm({ name: "", identifier: "", type: "host" });
      await reload();
    } catch (err) {
      setAlert(err instanceof ApiError ? err.message : "Unable to create asset.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <DashboardShell title="Assets" subtitle="Targets scanned within this project.">
      {(alert || error) && <FormAlert message={alert || error} />}
      {success && <FormAlert message={success} variant="success" />}
      <ProjectNav projectName={project?.name} active="assets" />

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6">
          <h2 className="mb-4 text-lg font-semibold text-brand-100">Project assets</h2>
          {loading ? (
            <p className="text-brand-500">Loading...</p>
          ) : assets.length === 0 ? (
            <p className="text-brand-500">No assets yet. Add a host, domain, or IP to scan.</p>
          ) : (
            <ul className="space-y-3">
              {assets.map((asset) => (
                <li
                  key={asset.id}
                  className="flex items-center justify-between rounded-lg border border-brand-800/50 px-4 py-3"
                >
                  <div>
                    <p className="font-medium text-brand-100">{asset.name}</p>
                    <p className="text-sm text-brand-500">{asset.identifier ?? asset.type}</p>
                  </div>
                  <Link
                    to={`/projects/${projectId}/assets/${asset.id}/scans`}
                    className="link-glow inline-flex items-center gap-1 text-sm"
                  >
                    <Server size={16} />
                    Scans
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
          <h2 className="text-lg font-semibold text-brand-100">Add asset</h2>
          <div>
            <label htmlFor="name" className="terminal-text mb-2 block">name</label>
            <input id="name" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} className="input-field" />
            <FormError message={errors.name} />
          </div>
          <div>
            <label htmlFor="identifier" className="terminal-text mb-2 block">identifier</label>
            <input id="identifier" value={form.identifier} onChange={(e) => setForm((p) => ({ ...p, identifier: e.target.value }))} className="input-field" placeholder="example.com" />
          </div>
          <div>
            <label htmlFor="type" className="terminal-text mb-2 block">type</label>
            <select id="type" value={form.type} onChange={(e) => setForm((p) => ({ ...p, type: e.target.value }))} className="input-field">
              {ASSET_TYPES.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          <button type="submit" disabled={creating} className="btn-primary inline-flex w-full items-center justify-center gap-2">
            <Plus size={18} />
            {creating ? "Adding..." : "Add asset"}
          </button>
          <p className="flex items-center gap-2 text-xs text-brand-600">
            <Globe size={14} />
            Scans run against assets, not projects directly.
          </p>
        </motion.form>
      </div>
    </DashboardShell>
  );
}
