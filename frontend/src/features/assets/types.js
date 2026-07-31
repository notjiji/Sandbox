/** @typedef {'website'|'domain'|'public_ip'|'server'|'windows_server'|'docker_host'|'cloud_account'|'kubernetes_cluster'|'api_endpoint'|'mobile_application'|'git_repository'|'email_domain'|'s3_bucket'|'azure_subscription'} AssetType */
/** @typedef {'active'|'inactive'|'archived'} AssetStatus */

/** Child asset type → required parent asset type. */
export const CHILD_PARENT_TYPES = {
  public_ip: "website",
  email_domain: "domain",
  s3_bucket: "cloud_account",
};

/** Child assets that require a parent. */
export const CHILD_ASSET_TYPES = Object.keys(CHILD_PARENT_TYPES);

/** Root assets registered directly under a project. */
export const ROOT_ASSET_TYPES = [
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

export const ASSET_TYPES = [...ROOT_ASSET_TYPES, ...CHILD_ASSET_TYPES];

export const ASSET_STATUSES = ["active", "inactive", "archived"];

export const ASSET_TYPE_LABELS = {
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

/** Grouped options for the asset type selector. */
export const ASSET_TYPE_GROUPS = [
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

export const IDENTIFIER_PLACEHOLDERS = {
  website: "https://example.com",
  domain: "example.com",
  public_ip: "203.0.113.10",
  server: "host.example.com",
  windows_server: "win-host.example.com",
  docker_host: "docker.example.com",
  cloud_account: "123456789012",
  kubernetes_cluster: "prod-cluster",
  api_endpoint: "https://api.example.com/v1",
  mobile_application: "com.example.app",
  git_repository: "github.com/org/repo",
  email_domain: "mail.example.com",
  s3_bucket: "my-app-bucket",
  azure_subscription: "00000000-0000-0000-0000-000000000000",
};
