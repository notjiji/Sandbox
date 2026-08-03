export interface ProjectSummary {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description?: string | null;
  created_by?: string | null;
  is_active: boolean;
}

export interface CreateProjectRequest {
  name: string;
  slug?: string;
  description?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface ProjectListData {
  items: ProjectSummary[];
}
