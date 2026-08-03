import {
  ASSET_CRITICALITY_LABELS,
  ASSET_ENVIRONMENT_LABELS,
  ASSET_STATUS_LABELS,
  ASSET_TYPE_LABELS,
} from "../types";
import { criticalityClass, environmentClass, statusClass } from "../utils";
import type {
  AssetCriticality,
  AssetEnvironment,
  AssetStatus,
  AssetType,
} from "@/shared/types/asset";

interface BadgeProps {
  label: string;
  className: string;
}

function Badge({ label, className }: BadgeProps) {
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${className}`}>
      {label}
    </span>
  );
}

interface AssetTypeBadgeProps {
  type: AssetType;
}

export function AssetTypeBadge({ type }: AssetTypeBadgeProps) {
  return (
    <Badge
      label={ASSET_TYPE_LABELS[type] ?? type}
      className="border-brand-600/40 bg-brand-900/50 text-brand-200"
    />
  );
}

interface AssetStatusBadgeProps {
  status: AssetStatus;
}

export function AssetStatusBadge({ status }: AssetStatusBadgeProps) {
  return (
    <Badge
      label={ASSET_STATUS_LABELS[status] ?? status}
      className={statusClass(status)}
    />
  );
}

interface AssetCriticalityBadgeProps {
  criticality: AssetCriticality;
}

export function AssetCriticalityBadge({ criticality }: AssetCriticalityBadgeProps) {
  return (
    <Badge
      label={ASSET_CRITICALITY_LABELS[criticality] ?? criticality}
      className={criticalityClass(criticality)}
    />
  );
}

interface AssetEnvironmentBadgeProps {
  environment: AssetEnvironment;
}

export function AssetEnvironmentBadge({ environment }: AssetEnvironmentBadgeProps) {
  return (
    <Badge
      label={ASSET_ENVIRONMENT_LABELS[environment] ?? environment}
      className={environmentClass(environment)}
    />
  );
}
