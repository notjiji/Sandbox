import type {
  AssetCriticality,
  AssetEnvironment,
  AssetFormState,
  AssetLinkType,
  AssetStatus,
  AssetSummary,
  AssetType,
} from "@/shared/types/asset";

/** Child asset type → allowed parent asset types. */
export const ALLOWED_PARENT_TYPES: Partial<Record<AssetType, AssetType[]>> = {
  public_ip: ["website", "domain"],
  email_domain: ["domain"],
  s3_bucket: ["cloud_account"],
  server: ["public_ip"],
  windows_server: ["public_ip"],
  docker_host: ["server", "windows_server"],
  website: ["docker_host", "server", "domain"],
  api_endpoint: ["website", "kubernetes_cluster"],
  kubernetes_cluster: ["cloud_account", "azure_subscription"],
};

export const REQUIRED_PARENT_TYPES: AssetType[] = [
  "public_ip",
  "email_domain",
  "s3_bucket",
  "server",
  "windows_server",
  "docker_host",
];

/** @deprecated Use ALLOWED_PARENT_TYPES */
export const CHILD_PARENT_TYPES: Partial<Record<AssetType, AssetType>> = {
  public_ip: "website",
  email_domain: "domain",
  s3_bucket: "cloud_account",
  server: "public_ip",
  windows_server: "public_ip",
  docker_host: "server",
  website: "docker_host",
  api_endpoint: "website",
  kubernetes_cluster: "cloud_account",
};

/** Child assets that may have a parent. */
export const CHILD_ASSET_TYPES = Object.keys(ALLOWED_PARENT_TYPES) as AssetType[];

/** Root assets registered directly under a project. */
export const ROOT_ASSET_TYPES: AssetType[] = [
  "website",
  "domain",
  "server",
  "windows_server",
  "docker_host",
  "cloud_account",
  "kubernetes_cluster",
  "api_endpoint",
  "mobile_application",
  "git_repository",
  "azure_subscription",
];

export const ASSET_TYPES: AssetType[] = [...ROOT_ASSET_TYPES, ...CHILD_ASSET_TYPES];

export const ASSET_STATUSES: AssetStatus[] = ["pending", "active", "archived", "deleted"];

export const ASSET_ENVIRONMENTS: AssetEnvironment[] = [
  "production",
  "staging",
  "development",
  "testing",
];

export const ASSET_CRITICALITIES: AssetCriticality[] = ["critical", "high", "medium", "low"];

export type AssetCategory =
  | "infrastructure"
  | "application"
  | "data"
  | "network"
  | "identity"
  | "endpoint"
  | "cloud"
  | "other";

export const ASSET_CATEGORIES: AssetCategory[] = [
  "infrastructure",
  "application",
  "data",
  "network",
  "identity",
  "endpoint",
  "cloud",
  "other",
];

export const ASSET_CATEGORY_LABELS: Record<AssetCategory, string> = {
  infrastructure: "Infrastructure",
  application: "Application",
  data: "Data",
  network: "Network",
  identity: "Identity",
  endpoint: "Endpoint",
  cloud: "Cloud",
  other: "Other",
};

export const DEFAULT_ASSET_CATEGORY_BY_TYPE: Partial<Record<AssetType, AssetCategory>> = {
  website: "application",
  api_endpoint: "application",
  mobile_application: "application",
  git_repository: "application",
  domain: "network",
  public_ip: "network",
  email_domain: "network",
  server: "infrastructure",
  windows_server: "infrastructure",
  docker_host: "infrastructure",
  kubernetes_cluster: "infrastructure",
  cloud_account: "cloud",
  azure_subscription: "cloud",
  s3_bucket: "cloud",
};

export const ASSET_LINK_TYPES: AssetLinkType[] = [
  "depends_on",
  "hosts",
  "runs_on",
  "exposes",
  "related",
];

export const ASSET_LINK_TYPE_LABELS: Record<AssetLinkType, string> = {
  depends_on: "Depends on",
  hosts: "Hosts",
  runs_on: "Runs on",
  exposes: "Exposes",
  related: "Related",
};

export const SCAN_STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  queued: "Queued",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

export const ASSET_TYPE_LABELS: Record<AssetType, string> = {
  website: "Website",
  domain: "Domain",
  public_ip: "Public IP",
  server: "Server",
  windows_server: "Windows Server",
  docker_host: "Docker Host",
  cloud_account: "Cloud Account",
  kubernetes_cluster: "Kubernetes Cluster",
  api_endpoint: "API Endpoint",
  mobile_application: "Mobile Application",
  git_repository: "Git Repository",
  email_domain: "Email Domain",
  s3_bucket: "S3 Bucket",
  azure_subscription: "Azure Subscription",
};

export const ASSET_STATUS_LABELS: Record<AssetStatus, string> = {
  pending: "Pending",
  active: "Active",
  archived: "Archived",
  deleted: "Deleted",
};

export const ASSET_ENVIRONMENT_LABELS: Record<AssetEnvironment, string> = {
  production: "Production",
  staging: "Staging",
  development: "Development",
  testing: "Testing",
};

export const ASSET_CRITICALITY_LABELS: Record<AssetCriticality, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

export const SERVER_CONNECTION_TYPES = ["ssh", "rdp", "winrm", "agent", "snmp", "other"] as const;
export type ServerConnectionType = (typeof SERVER_CONNECTION_TYPES)[number];

export const SERVER_CONNECTION_TYPE_LABELS: Record<ServerConnectionType, string> = {
  ssh: "SSH",
  rdp: "RDP",
  winrm: "WinRM",
  agent: "Agent",
  snmp: "SNMP",
  other: "Other",
};

/** Primary metadata key per asset type (stored in asset_metadata). */
export const PRIMARY_METADATA_KEYS: Record<AssetType, string> = {
  website: "url",
  domain: "domain",
  public_ip: "address",
  server: "hostname",
  windows_server: "hostname",
  docker_host: "hostname",
  cloud_account: "account_id",
  kubernetes_cluster: "cluster",
  api_endpoint: "endpoint",
  mobile_application: "bundle_id",
  git_repository: "repository",
  email_domain: "email_domain",
  s3_bucket: "bucket",
  azure_subscription: "subscription_id",
};

/** Grouped options for the asset type selector. */
export const ASSET_TYPE_GROUPS: Array<{ label: string; types: AssetType[] }> = [
  {
    label: "Web & DNS",
    types: ["website", "domain", "public_ip", "email_domain", "api_endpoint"],
  },
  {
    label: "Infrastructure",
    types: ["server", "windows_server", "docker_host", "kubernetes_cluster"],
  },
  {
    label: "Cloud",
    types: ["cloud_account", "azure_subscription", "s3_bucket"],
  },
  {
    label: "Application & Code",
    types: ["mobile_application", "git_repository"],
  },
];

export const METADATA_PLACEHOLDERS: Record<AssetType, string> = {
  website: "https://example.com",
  domain: "example.com",
  public_ip: "203.0.113.10",
  server: "prod-server",
  windows_server: "win-host",
  docker_host: "docker-host",
  cloud_account: "123456789012",
  kubernetes_cluster: "prod-cluster",
  api_endpoint: "https://api.example.com/v1",
  mobile_application: "com.example.app",
  git_repository: "github.com/org/repo",
  email_domain: "mail.example.com",
  s3_bucket: "my-app-bucket",
  azure_subscription: "00000000-0000-0000-0000-000000000000",
};

/** @deprecated Use PRIMARY_METADATA_KEYS */
export const IDENTIFIER_PLACEHOLDERS = METADATA_PLACEHOLDERS;

export function getPrimaryMetadataValue(asset: AssetSummary): string | null {
  const key = PRIMARY_METADATA_KEYS[asset.type];
  if (key && asset.metadata?.[key]) return asset.metadata[key];
  return null;
}

export function buildMetadataPayload(
  type: AssetType,
  primaryValue: string | undefined,
  extraMetadata: Record<string, string> = {},
): Record<string, string> {
  const payload = { ...extraMetadata };
  const key = PRIMARY_METADATA_KEYS[type];
  if (key && primaryValue?.trim()) {
    payload[key] = primaryValue.trim();
  }
  return payload;
}

export function assetToFormState(asset: AssetSummary): AssetFormState {
  const primaryKey = PRIMARY_METADATA_KEYS[asset.type];
  return {
    name: asset.name ?? "",
    description: asset.description ?? "",
    primary_value: primaryKey ? (asset.metadata?.[primaryKey] ?? "") : "",
    external_identifier: asset.external_identifier ?? "",
    business_unit: asset.business_unit ?? "",
    asset_category: asset.asset_category ?? DEFAULT_ASSET_CATEGORY_BY_TYPE[asset.type] ?? "",
    os: asset.metadata?.os ?? "",
    connection_type: asset.metadata?.connection_type ?? "ssh",
    allow_private_ip: false,
    type: asset.type,
    status: asset.status,
    environment: asset.environment,
    criticality: asset.criticality,
    owner: asset.owner ?? "",
    tags: (asset.tags ?? []).join(", "),
    parent_id: asset.parent_id ?? "",
  };
}

export const HOST_TYPES_WITH_OS: AssetType[] = ["server", "windows_server"];

export function typeNeedsOsFields(type: AssetType): boolean {
  return HOST_TYPES_WITH_OS.includes(type);
}
