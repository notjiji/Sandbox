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
  ASSET_CRITICALITIES,
  ASSET_CRITICALITY_LABELS,
  ASSET_ENVIRONMENTS,
  ASSET_ENVIRONMENT_LABELS,
  ASSET_STATUSES,
  ASSET_STATUS_LABELS,
  ASSET_TYPE_GROUPS,
  ASSET_TYPE_LABELS,
  CHILD_ASSET_TYPES,
  CHILD_PARENT_TYPES,
  METADATA_PLACEHOLDERS,
  PRIMARY_METADATA_KEYS,
  buildMetadataPayload,
  getPrimaryMetadataValue,
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

const EMPTY_FORM = {
  name: "",
  description: "",
  primary_value: "",
  type: "website",
  status: "pending",
  environment: "production",
  criticality: "medium",
  owner: "",
  tags: "",
  parent_id: "",
};

export default function Assets() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const { assets, loading, error, reload } = useProjectAssets(projectId);
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [creating, setCreating] = useState(false);

  const isChildType = CHILD_ASSET_TYPES.includes(form.type);
  const requiredParentType = CHILD_PARENT_TYPES[form.type];
  const primaryMetadataKey = PRIMARY_METADATA_KEYS[form.type];

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
      const tags = form.tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);

      await assetsApi.create(projectId, {
        name: form.name.trim(),
        description: form.description.trim() || null,
        type: form.type,
        status: form.status,
        environment: form.environment,
        criticality: form.criticality,
        owner: form.owner.trim() || null,
        metadata: buildMetadataPayload(form.type, form.primary_value),
        tags,
        parent_id: isChildType ? form.parent_id : null,
      });
      setSuccess("Asset created.");
      setForm(EMPTY_FORM);
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
    const primaryValue = getPrimaryMetadataValue(asset);
    const canScan = asset.status === "active";

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
                {primaryValue ? ` · ${primaryValue}` : ""}
              </p>
              <p className="mt-1 text-xs text-brand-600">
                {ASSET_STATUS_LABELS[asset.status] ?? asset.status}
                {" · "}
                {ASSET_ENVIRONMENT_LABELS[asset.environment] ?? asset.environment}
                {" · "}
                {ASSET_CRITICALITY_LABELS[asset.criticality] ?? asset.criticality}
                {asset.owner ? ` · ${asset.owner}` : ""}
              </p>
              {asset.tags?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {asset.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-brand-900/60 px-2 py-0.5 text-xs text-brand-400"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
          {canScan ? (
            <Link
              to={`/projects/${projectId}/assets/${asset.id}/scans`}
              className="link-glow text-sm"
            >
              Scans
            </Link>
          ) : (
            <span className="text-xs text-brand-600">Activate to scan</span>
          )}
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
              No assets yet. Register websites, servers, cloud accounts, and more — then attach
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
            <label htmlFor="description" className="terminal-text mb-2 block">description</label>
            <textarea
              id="description"
              value={form.description}
              onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
              className="input-field min-h-20"
            />
          </div>

          <div>
            <label htmlFor="primary_value" className="terminal-text mb-2 block">
              {primaryMetadataKey ?? "metadata"}
            </label>
            <input
              id="primary_value"
              value={form.primary_value}
              onChange={(e) => setForm((prev) => ({ ...prev, primary_value: e.target.value }))}
              className="input-field"
              placeholder={METADATA_PLACEHOLDERS[form.type] ?? "example.com"}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="status" className="terminal-text mb-2 block">status</label>
              <select
                id="status"
                value={form.status}
                onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value }))}
                className="input-field"
              >
                {ASSET_STATUSES.filter((status) => status !== "deleted").map((status) => (
                  <option key={status} value={status}>
                    {ASSET_STATUS_LABELS[status]}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="environment" className="terminal-text mb-2 block">environment</label>
              <select
                id="environment"
                value={form.environment}
                onChange={(e) => setForm((prev) => ({ ...prev, environment: e.target.value }))}
                className="input-field"
              >
                {ASSET_ENVIRONMENTS.map((environment) => (
                  <option key={environment} value={environment}>
                    {ASSET_ENVIRONMENT_LABELS[environment]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="criticality" className="terminal-text mb-2 block">criticality</label>
              <select
                id="criticality"
                value={form.criticality}
                onChange={(e) => setForm((prev) => ({ ...prev, criticality: e.target.value }))}
                className="input-field"
              >
                {ASSET_CRITICALITIES.map((criticality) => (
                  <option key={criticality} value={criticality}>
                    {ASSET_CRITICALITY_LABELS[criticality]}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="owner" className="terminal-text mb-2 block">owner</label>
              <input
                id="owner"
                value={form.owner}
                onChange={(e) => setForm((prev) => ({ ...prev, owner: e.target.value }))}
                className="input-field"
                placeholder="Infrastructure Team"
              />
            </div>
          </div>

          <div>
            <label htmlFor="tags" className="terminal-text mb-2 block">tags</label>
            <input
              id="tags"
              value={form.tags}
              onChange={(e) => setForm((prev) => ({ ...prev, tags: e.target.value }))}
              className="input-field"
              placeholder="customer-facing, api, linux"
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
