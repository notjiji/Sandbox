import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Cloud,
  Code2,
  Container,
  Database,
  Globe,
  Mail,
  Network,
  Plus,
  Server,
  Smartphone,
  Terminal,
} from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError } from "@/shared/api/client";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import { assetsApi } from "../api";
import { useProjectAssets } from "../hooks";
import {
  ASSET_TYPE_GROUPS,
  ASSET_TYPE_LABELS,
  CHILD_ASSET_TYPES,
  CHILD_PARENT_TYPES,
  IDENTIFIER_PLACEHOLDERS,
} from "../types";

const TYPE_ICONS = {
  website: Globe,
  domain: Network,
  public_ip: Network,
  server: Server,
  windows_server: Terminal,
  docker_host: Container,
  cloud_account: Cloud,
  kubernetes_cluster: Container,
  api_endpoint: Code2,
  mobile_application: Smartphone,
  git_repository: Code2,
  email_domain: Mail,
  s3_bucket: Database,
  azure_subscription: Cloud,
};

export default function Assets() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const { assets, loading, error, reload } = useProjectAssets(projectId);
  const [form, setForm] = useState({
    name: "",
    identifier: "",
    type: "website",
    parent_id: "",
  });
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [creating, setCreating] = useState(false);

  const isChildType = CHILD_ASSET_TYPES.includes(form.type);
  const requiredParentType = CHILD_PARENT_TYPES[form.type];

  const parentOptions = useMemo(
    () => assets.filter((asset) => asset.type === requiredParentType),
    [assets, requiredParentType],
  );

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
    if (isChildType && !form.parent_id) {
      setErrors({
        parent_id: `Select a parent ${ASSET_TYPE_LABELS[requiredParentType]?.toLowerCase() ?? requiredParentType}`,
      });
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
        parent_id: isChildType ? form.parent_id : null,
      });
      setSuccess("Asset created.");
      setForm({ name: "", identifier: "", type: "website", parent_id: "" });
      await reload();
    } catch (err) {
      setAlert(err instanceof ApiError ? err.message : "Unable to create asset.");
    } finally {
      setCreating(false);
    }
  };

  const renderAsset = (asset, depth = 0) => {
    const Icon = TYPE_ICONS[asset.type] ?? Globe;
    const children = assets.filter((item) => item.parent_id === asset.id);

    return (
      <li key={asset.id}>
        <div
          className="flex items-center justify-between rounded-lg border border-brand-800/50 px-4 py-3"
          style={{ marginLeft: depth * 16 }}
        >
          <div className="flex items-start gap-3">
            <Icon size={18} className="mt-0.5 text-brand-400" />
            <div>
              <p className="font-medium text-brand-100">{asset.name}</p>
              <p className="text-sm text-brand-500">
                {ASSET_TYPE_LABELS[asset.type] ?? asset.type}
                {asset.identifier ? ` · ${asset.identifier}` : ""}
              </p>
            </div>
          </div>
          <Link
            to={`/projects/${projectId}/assets/${asset.id}/scans`}
            className="link-glow text-sm"
          >
            Scans
          </Link>
        </div>
        {children.length > 0 && (
          <ul className="mt-2 space-y-2">
            {children.map((child) => renderAsset(child, depth + 1))}
          </ul>
        )}
      </li>
    );
  };

  const rootAssets = assets.filter((asset) => !asset.parent_id);

  return (
    <DashboardShell title="Assets" subtitle="Digital assets owned by this project.">
      {(alert || error) && <FormAlert message={alert || error} />}
      {success && <FormAlert message={success} variant="success" />}
      <ProjectNav projectName={project?.name} active="assets" />

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6">
          <h2 className="mb-4 text-lg font-semibold text-brand-100">Project assets</h2>
          {loading ? (
            <p className="text-brand-500">Loading...</p>
          ) : rootAssets.length === 0 ? (
            <p className="text-brand-500">
              No assets yet. Add websites, domains, servers, cloud accounts, and more — then attach
              child assets such as public IPs, email domains, or S3 buckets.
            </p>
          ) : (
            <ul className="space-y-3">{rootAssets.map((asset) => renderAsset(asset))}</ul>
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
            <label htmlFor="type" className="terminal-text mb-2 block">type</label>
            <select
              id="type"
              value={form.type}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  type: e.target.value,
                  parent_id: CHILD_ASSET_TYPES.includes(e.target.value) ? prev.parent_id : "",
                }))
              }
              className="input-field"
            >
              {ASSET_TYPE_GROUPS.map((group) => (
                <optgroup key={group.label} label={group.label}>
                  {group.types.map((type) => (
                    <option key={type} value={type}>
                      {ASSET_TYPE_LABELS[type]}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          {isChildType && (
            <div>
              <label htmlFor="parent_id" className="terminal-text mb-2 block">
                parent {ASSET_TYPE_LABELS[requiredParentType]?.toLowerCase() ?? requiredParentType}
              </label>
              <select
                id="parent_id"
                value={form.parent_id}
                onChange={(e) => setForm((prev) => ({ ...prev, parent_id: e.target.value }))}
                className="input-field"
              >
                <option value="">
                  Select {ASSET_TYPE_LABELS[requiredParentType]?.toLowerCase() ?? requiredParentType}...
                </option>
                {parentOptions.map((parent) => (
                  <option key={parent.id} value={parent.id}>
                    {parent.name}
                  </option>
                ))}
              </select>
              <FormError message={errors.parent_id} />
            </div>
          )}

          <div>
            <label htmlFor="name" className="terminal-text mb-2 block">name</label>
            <input
              id="name"
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              className="input-field"
            />
            <FormError message={errors.name} />
          </div>
          <div>
            <label htmlFor="identifier" className="terminal-text mb-2 block">identifier</label>
            <input
              id="identifier"
              value={form.identifier}
              onChange={(e) => setForm((prev) => ({ ...prev, identifier: e.target.value }))}
              className="input-field"
              placeholder={IDENTIFIER_PLACEHOLDERS[form.type] ?? "example.com"}
            />
          </div>
          <button
            type="submit"
            disabled={creating}
            className="btn-primary inline-flex w-full items-center justify-center gap-2"
          >
            <Plus size={18} />
            {creating ? "Adding..." : "Add asset"}
          </button>
        </motion.form>
      </div>
    </DashboardShell>
  );
}
