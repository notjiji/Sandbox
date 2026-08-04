import { apiRequest } from "@/shared/api/client";
import type {
  CreateProjectRequest,
  ProjectListData,
  ProjectSummary,
  UpdateProjectRequest,
} from "@/shared/types/project";
import type { MessageResponse } from "@/shared/types/auth";

export const projectsApi = {
  list: () => apiRequest<ProjectListData>("/projects", { auth: true }),

  create: (data: CreateProjectRequest) =>
    apiRequest<ProjectSummary>("/projects", {
      method: "POST",
      body: data,
      auth: true,
    }),

  get: (projectId: string) =>
    apiRequest<ProjectSummary>(`/projects/${projectId}`, { auth: true }),

  update: (projectId: string, data: UpdateProjectRequest) =>
    apiRequest<ProjectSummary>(`/projects/${projectId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),

  delete: (projectId: string) =>
    apiRequest<MessageResponse>(`/projects/${projectId}`, {
      method: "DELETE",
      auth: true,
    }),
};
