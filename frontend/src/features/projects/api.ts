import { apiRequest } from "@/shared/api/client";
import type {
  CreateProjectRequest,
  ProjectListData,
  ProjectSummary,
  UpdateProjectRequest,
} from "@/shared/types/project";
import type { ProjectActivityData, ProjectOverview } from "@/shared/types/project-overview";
import type { MessageResponse } from "@/shared/types/auth";

export const projectsApi = {
  list: (includeInactive = false) =>
    apiRequest<ProjectListData>(
      `/projects${includeInactive ? "?include_inactive=true" : ""}`,
      { auth: true },
    ),

  create: (data: CreateProjectRequest) =>
    apiRequest<ProjectSummary>("/projects", {
      method: "POST",
      body: data,
      auth: true,
    }),

  get: (projectId: string) =>
    apiRequest<ProjectSummary>(`/projects/${projectId}`, { auth: true }),

  getOverview: (projectId: string) =>
    apiRequest<ProjectOverview>(`/projects/${projectId}/overview`, { auth: true }),

  getActivity: (projectId: string, page = 1, limit = 20) =>
    apiRequest<ProjectActivityData>(
      `/projects/${projectId}/activity?page=${page}&limit=${limit}`,
      { auth: true },
    ),

  update: (projectId: string, data: UpdateProjectRequest) =>
    apiRequest<ProjectSummary>(`/projects/${projectId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),

  archive: (projectId: string) =>
    apiRequest<ProjectSummary>(`/projects/${projectId}/archive`, {
      method: "PATCH",
      auth: true,
    }),

  restore: (projectId: string) =>
    apiRequest<ProjectSummary>(`/projects/${projectId}/restore`, {
      method: "PATCH",
      auth: true,
    }),

  delete: (projectId: string) =>
    apiRequest<MessageResponse>(`/projects/${projectId}`, {
      method: "DELETE",
      auth: true,
    }),
};
