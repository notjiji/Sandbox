import type {
  AssetCriticality,
  AssetEnvironment,
  AssetFormState,
  AssetStatus,
  AssetSummary,
  AssetType,
} from "@/shared/types/asset";

/** Child asset type → required parent asset type. */
export const CHILD_PARENT_TYPES: Partial<Record<AssetType, AssetType>> = {
  public_ip: "website",
  email_domain: "domain",
  s3_bucket: "cloud_account",
};

/** Child assets that require a parent. */
export const CHILD_ASSET_TYPES = Object.keys(CHILD_PARENT_TYPES) as AssetType[];

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
