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
export type AssetCategory =
  | "infrastructure"
  | "application"
  | "data"
  | "network"
  | "identity"
  | "endpoint"
  | "cloud"
  | "other";

export type ScanStatus =
  | "pending"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface AssetActorSummary {
  id?: string | null;
  name?: string | null;
  email?: string | null;
}

export type AssetLinkType = "depends_on" | "hosts" | "runs_on" | "exposes" | "related";

export interface AssetGraphNode {
  id: string;
  name: string;
  type: AssetType;
  external_identifier?: string | null;
  is_current?: boolean;
  depth?: number;
}

export interface AssetGraphEdge {
  source: string;
  target: string;
  kind: "parent" | "link";
  link_type?: AssetLinkType | null;
  label?: string | null;
}

export interface AssetRelationshipGraph {
  nodes: AssetGraphNode[];
  edges: AssetGraphEdge[];
}

export interface AssetLinkSummary {
  id: string;
  link_type: AssetLinkType;
  label?: string | null;
  direction: "inbound" | "outbound";
  asset: AssetSummary;
}

export interface AssetRelationships {
  parent?: AssetSummary | null;
  ancestors: AssetSummary[];
  children: AssetSummary[];
  links: AssetLinkSummary[];
  graph: AssetRelationshipGraph;
  descendants_count: number;
}

export interface CreateAssetLinkRequest {
  target_asset_id: string;
  link_type?: AssetLinkType;
  label?: string;
}

export interface AssetSummary {
  id: string;
  organization_id: string;
  organization_name?: string | null;
  project_id: string;
  project_name?: string | null;
  parent_id?: string | null;
  parent_name?: string | null;
  name: string;
  description?: string | null;
  type: AssetType;
  external_identifier?: string | null;
  status: AssetStatus;
  environment: AssetEnvironment;
  criticality: AssetCriticality;
  business_unit?: string | null;
  owner?: string | null;
  asset_category?: AssetCategory | null;
  metadata: Record<string, string>;
  tags: string[];
  children_count?: number;

  current_risk_score?: number | null;
  security_grade?: string | null;
  last_scan_at?: string | null;
  last_successful_scan_at?: string | null;
  last_scan_status?: ScanStatus | string | null;
  findings_count?: number;
  critical_findings_count?: number;

  created_at?: string | null;
  updated_at?: string | null;
  archived_at?: string | null;
  archived_by?: AssetActorSummary | null;
  created_by?: AssetActorSummary | null;
  last_modified_by?: AssetActorSummary | null;
}

export type AssetSortField =
  | "name"
  | "created_at"
  | "updated_at"
  | "criticality"
  | "environment"
  | "type";

export type SortOrder = "asc" | "desc";

export interface AssetTagFacet {
  tag: string;
  count: number;
}

export interface AssetTagListData {
  items: AssetTagFacet[];
}

export interface AssetSavedFilterState {
  search: string;
  tags: string[];
  type: string;
  status: string;
  environment: string;
  criticality: string;
  asset_category: string;
  sort: AssetSortField;
  order: SortOrder;
}

export interface AssetSavedFilterSummary {
  id: string;
  name: string;
  filters: AssetSavedFilterState;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AssetSavedFilterListData {
  items: AssetSavedFilterSummary[];
}

export interface CreateAssetSavedFilterRequest {
  name: string;
  filters: AssetSavedFilterState;
}

export type AssetBulkAction =
  | "archive"
  | "delete"
  | "assign_tags"
  | "change_owner"
  | "launch_scan"
  | "export";

export interface AssetBulkActionRequest {
  asset_ids: string[];
  action: AssetBulkAction;
  tags?: string[];
  tag_mode?: "add" | "replace";
  owner?: string;
  scan_type?: import("@/shared/types/scan").ScanType;
}

export interface AssetBulkActionItemResult {
  asset_id: string;
  success: boolean;
  message?: string | null;
  scan_id?: string | null;
}

export interface AssetBulkActionResponse {
  action: AssetBulkAction;
  total: number;
  succeeded: number;
  failed: number;
  results: AssetBulkActionItemResult[];
  export_items: AssetSummary[];
}

export interface AssetListQuery {
  page?: number;
  limit?: number;
  status?: AssetStatus;
  type?: AssetType;
  criticality?: AssetCriticality;
  environment?: AssetEnvironment;
  asset_category?: AssetCategory;
  search?: string;
  tags?: string[];
  sort?: AssetSortField;
  order?: SortOrder;
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
  external_identifier?: string;
  business_unit?: string;
  asset_category?: AssetCategory;
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
  external_identifier?: string;
  business_unit?: string;
  asset_category?: AssetCategory;
  metadata?: Record<string, string>;
  tags?: string[];
  parent_id?: string | null;
}

export interface AssetFormState {
  name: string;
  description: string;
  primary_value: string;
  external_identifier: string;
  business_unit: string;
  asset_category: AssetCategory | "";
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
