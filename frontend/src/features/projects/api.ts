import { apiRequest } from "@/shared/api/client";
import type { ApiEnvelope } from "@/shared/types/api";
import type {
  CreateProjectRequest,
  ProjectListData,
  ProjectSummary,
  UpdateProjectRequest,
} from "@/shared/types/project";
import type { MessageResponse } from "@/shared/types/auth";

export const projectsApi = {
  list: () => apiRequest<ApiEnvelope<ProjectListData>>("/projects", { auth: true }),

  create: (data: CreateProjectRequest) =>
    apiRequest<ApiEnvelope<ProjectSummary>>("/projects", {
      method: "POST",
      body: data,
      auth: true,
    }),

  get: (projectId: string) =>
    apiRequest<ApiEnvelope<ProjectSummary>>(`/projects/${projectId}`, { auth: true }),

  update: (projectId: string, data: UpdateProjectRequest) =>
    apiRequest<ApiEnvelope<ProjectSummary>>(`/projects/${projectId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),

  delete: (projectId: string) =>
    apiRequest<ApiEnvelope<MessageResponse>>(`/projects/${projectId}`, {
      method: "DELETE",
      auth: true,
    }),
};
