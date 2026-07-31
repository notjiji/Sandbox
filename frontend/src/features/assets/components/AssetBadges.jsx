import {
  ASSET_CRITICALITY_LABELS,
  ASSET_ENVIRONMENT_LABELS,
  ASSET_STATUS_LABELS,
  ASSET_TYPE_LABELS,
} from "../types";
import { criticalityClass, environmentClass, statusClass } from "../utils";

function Badge({ label, className }) {
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${className}`}>
      {label}
    </span>
  );
}

export function AssetTypeBadge({ type }) {
  return (
    <Badge
      label={ASSET_TYPE_LABELS[type] ?? type}
      className="border-brand-600/40 bg-brand-900/50 text-brand-200"
    />
  );
}

export function AssetStatusBadge({ status }) {
  return (
    <Badge
      label={ASSET_STATUS_LABELS[status] ?? status}
      className={statusClass(status)}
    />
  );
}

export function AssetCriticalityBadge({ criticality }) {
  return (
    <Badge
      label={ASSET_CRITICALITY_LABELS[criticality] ?? criticality}
      className={criticalityClass(criticality)}
    />
  );
}

export function AssetEnvironmentBadge({ environment }) {
  return (
    <Badge
      label={ASSET_ENVIRONMENT_LABELS[environment] ?? environment}
      className={environmentClass(environment)}
    />
  );
}
