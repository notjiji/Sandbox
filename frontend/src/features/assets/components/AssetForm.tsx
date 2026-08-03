import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Plus, Save } from "lucide-react";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError } from "@/shared/api/client";
import type { ValidationErrors } from "@/shared/types/api";
import type {
  AssetFormState,
  AssetStatus,
  AssetSummary,
  AssetType,
  CreateAssetRequest,
  UpdateAssetRequest,
} from "@/shared/types/asset";
import { assetsApi } from "../api";
import {
  ASSET_CRITICALITIES,
  ASSET_CRITICALITY_LABELS,
  ASSET_ENVIRONMENTS,
  ASSET_ENVIRONMENT_LABELS,
  ASSET_STATUS_LABELS,
  ASSET_TYPE_GROUPS,
  ASSET_TYPE_LABELS,
  CHILD_ASSET_TYPES,
  CHILD_PARENT_TYPES,
  METADATA_PLACEHOLDERS,
  PRIMARY_METADATA_KEYS,
  SERVER_CONNECTION_TYPES,
  SERVER_CONNECTION_TYPE_LABELS,
  assetToFormState,
  buildMetadataPayload,
  typeNeedsOsFields,
} from "../types";

const EDITABLE_STATUSES: AssetStatus[] = ["pending", "active"];

const EMPTY_FORM: AssetFormState = {
  name: "",
  description: "",
  primary_value: "",
  os: "",
  connection_type: "ssh",
  allow_private_ip: false,
  type: "website",
  status: "pending",
  environment: "production",
  criticality: "medium",
  owner: "",
  tags: "",
  parent_id: "",
};

interface CreateAssetPayload extends CreateAssetRequest {
  allow_private_ip?: boolean;
}

interface AssetFormProps {
  mode?: "create" | "edit";
  projectId: string;
  assetId?: string;
  asset?: AssetSummary;
  parentAssets?: AssetSummary[];
  onSuccess?: () => void;
  title?: string;
  submitLabel?: string;
}

export default function AssetForm({
  mode = "create",
  projectId,
  assetId,
  asset,
  parentAssets = [],
  onSuccess,
  title,
  submitLabel,
}: AssetFormProps) {
  const [form, setForm] = useState<AssetFormState>(EMPTY_FORM);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [alert, setAlert] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (mode === "edit" && asset) {
      setForm(assetToFormState(asset));
    }
  }, [mode, asset]);

  const isChildType = CHILD_ASSET_TYPES.includes(form.type);
  const isPublicIpType = form.type === "public_ip";
  const needsOsFields = typeNeedsOsFields(form.type);
  const requiredParentType = CHILD_PARENT_TYPES[form.type];
  const primaryMetadataKey = PRIMARY_METADATA_KEYS[form.type];
  const isEdit = mode === "edit";
  const showStatusField = !isEdit || EDITABLE_STATUSES.includes(form.status);

  const parentOptions = useMemo(
    () => parentAssets.filter((item) => item.type === requiredParentType && item.id !== assetId),
    [parentAssets, requiredParentType, assetId],
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setErrors({ name: "Asset name is required" });
      return;
    }
    if (isChildType && !form.parent_id) {
      const parentLabel = requiredParentType
        ? (ASSET_TYPE_LABELS[requiredParentType]?.toLowerCase() ?? requiredParentType)
        : "parent";
      setErrors({
        parent_id: `Select a parent ${parentLabel}`,
      });
      return;
    }

    setSubmitting(true);
    setAlert("");
    setErrors({});
    try {
      const tags = form.tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);

      const extraMetadata: Record<string, string> = {};
      if (needsOsFields) {
        extraMetadata.os = form.os.trim();
        extraMetadata.connection_type = form.connection_type;
      }

      const payload: CreateAssetPayload & UpdateAssetRequest = {
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        type: form.type,
        environment: form.environment,
        criticality: form.criticality,
        owner: form.owner.trim() || undefined,
        metadata: buildMetadataPayload(form.type, form.primary_value, extraMetadata),
        tags,
        allow_private_ip: isPublicIpType ? form.allow_private_ip : false,
        parent_id: isChildType ? form.parent_id : undefined,
      };
      if (showStatusField) {
        payload.status = form.status;
      }

      if (isEdit && assetId) {
        await assetsApi.update(projectId, assetId, payload);
      } else {
        await assetsApi.create(projectId, payload);
        setForm(EMPTY_FORM);
      }
      onSuccess?.();
    } catch (err) {
      setAlert(
        err instanceof ApiError ? err.message : `Unable to ${isEdit ? "update" : "create"} asset.`,
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <motion.form
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      onSubmit={handleSubmit}
      className="glass-panel h-fit space-y-4 p-6"
    >
      <h2 className="text-lg font-semibold text-brand-100">
        {title ?? (isEdit ? "Edit asset" : "Add asset")}
      </h2>
      {alert && <FormAlert message={alert} />}

      <div>
        <label htmlFor="type" className="terminal-text mb-2 block">
          type
        </label>
        <select
          id="type"
          value={form.type}
          disabled={isEdit}
          onChange={(e) =>
            setForm((prev) => ({
              ...prev,
              type: e.target.value as AssetType,
              parent_id: CHILD_ASSET_TYPES.includes(e.target.value as AssetType)
                ? prev.parent_id
                : "",
            }))
          }
          className="input-field disabled:opacity-60"
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

      {isChildType && requiredParentType && (
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
        <label htmlFor="name" className="terminal-text mb-2 block">
          name
        </label>
        <input
          id="name"
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

      {needsOsFields && (
        <>
          <div>
            <label htmlFor="os" className="terminal-text mb-2 block">
              operating system
            </label>
            <input
              id="os"
              value={form.os}
              onChange={(e) => setForm((prev) => ({ ...prev, os: e.target.value }))}
              className="input-field"
              placeholder="Ubuntu 24.04"
            />
          </div>
          <div>
            <label htmlFor="connection_type" className="terminal-text mb-2 block">
              connection type
            </label>
            <select
              id="connection_type"
              value={form.connection_type}
              onChange={(e) => setForm((prev) => ({ ...prev, connection_type: e.target.value }))}
              className="input-field"
            >
              {SERVER_CONNECTION_TYPES.map((type) => (
                <option key={type} value={type}>
                  {SERVER_CONNECTION_TYPE_LABELS[type]}
                </option>
              ))}
            </select>
          </div>
        </>
      )}

      {isPublicIpType && (
        <label className="flex items-center gap-2 text-sm text-brand-400">
          <input
            type="checkbox"
            checked={form.allow_private_ip}
            onChange={(e) => setForm((prev) => ({ ...prev, allow_private_ip: e.target.checked }))}
          />
          Allow private IPv4 addresses
        </label>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {showStatusField ? (
          <div>
            <label htmlFor="status" className="terminal-text mb-2 block">
              status
            </label>
            <select
              id="status"
              value={form.status}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, status: e.target.value as AssetStatus }))
              }
              className="input-field"
            >
              {EDITABLE_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {ASSET_STATUS_LABELS[status]}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <div>
            <p className="terminal-text mb-2 block text-xs text-brand-500">status</p>
            <p className="text-brand-200">{ASSET_STATUS_LABELS[form.status] ?? form.status}</p>
            <p className="mt-1 text-xs text-brand-500">
              Use Restore on the detail page to change lifecycle status.
            </p>
          </div>
        )}
        <div>
          <label htmlFor="environment" className="terminal-text mb-2 block">
            environment
          </label>
          <select
            id="environment"
            value={form.environment}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                environment: e.target.value as AssetFormState["environment"],
              }))
            }
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
          <label htmlFor="criticality" className="terminal-text mb-2 block">
            criticality
          </label>
          <select
            id="criticality"
            value={form.criticality}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                criticality: e.target.value as AssetFormState["criticality"],
              }))
            }
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
          <label htmlFor="owner" className="terminal-text mb-2 block">
            owner
          </label>
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
        <label htmlFor="tags" className="terminal-text mb-2 block">
          tags
        </label>
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
        disabled={submitting}
        className="btn-primary inline-flex w-full items-center justify-center gap-2"
      >
        {isEdit ? <Save size={18} /> : <Plus size={18} />}
        {submitting
          ? isEdit
            ? "Saving..."
            : "Adding..."
          : (submitLabel ?? (isEdit ? "Save changes" : "Add asset"))}
      </button>
    </motion.form>
  );
}
