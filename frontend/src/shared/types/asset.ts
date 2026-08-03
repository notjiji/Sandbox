export type AssetType =
  | "website"
  | "domain"
  | "public_ip"
  | "server"
  | "windows_server"
  | "docker_host"
  | "cloud_account"
  | "kubernetes_cluster"
  | "api_endpoint"
  | "mobile_application"
  | "git_repository"
  | "email_domain"
  | "s3_bucket"
  | "azure_subscription";

export type AssetStatus = "pending" | "active" | "archived" | "deleted";
export type AssetEnvironment = "production" | "staging" | "development" | "testing";
export type AssetCriticality = "critical" | "high" | "medium" | "low";

export interface AssetSummary {
  id: string;
  organization_id: string;
  project_id: string;
  parent_id?: string | null;
  parent_name?: string | null;
  name: string;
  description?: string | null;
  type: AssetType;
  status: AssetStatus;
  environment: AssetEnvironment;
  criticality: AssetCriticality;
  owner?: string | null;
  metadata: Record<string, string>;
  tags: string[];
  created_by?: string | null;
  children_count?: number;
}

export interface AssetListQuery {
  page?: number;
  limit?: number;
  status?: AssetStatus;
  type?: AssetType;
  criticality?: AssetCriticality;
  environment?: AssetEnvironment;
  search?: string;
  roots_only?: boolean;
  parent_id?: string;
}

export interface CreateAssetRequest {
  name: string;
  description?: string;
  type: AssetType;
  status?: AssetStatus;
  environment?: AssetEnvironment;
  criticality?: AssetCriticality;
  owner?: string;
  metadata?: Record<string, string>;
  tags?: string[];
  parent_id?: string;
}

export interface UpdateAssetRequest {
  name?: string;
  description?: string;
  type?: AssetType;
  status?: AssetStatus;
  environment?: AssetEnvironment;
  criticality?: AssetCriticality;
  owner?: string;
  metadata?: Record<string, string>;
  tags?: string[];
  parent_id?: string | null;
}

export interface AssetFormState {
  name: string;
  description: string;
  primary_value: string;
  os: string;
  connection_type: string;
  allow_private_ip: boolean;
  type: AssetType;
  status: AssetStatus;
  environment: AssetEnvironment;
  criticality: AssetCriticality;
  owner: string;
  tags: string;
  parent_id: string;
}

export interface AssetListData {
  items: AssetSummary[];
  total: number;
  page: number;
  limit: number;
}
