import { apiRequest } from "@/shared/api/client";
import type { ApiEnvelope } from "@/shared/types/api";
import type { ProjectRisk } from "@/shared/types/risk";

export const riskApi = {
  getProjectRisk: (projectId: string) =>
    apiRequest<ApiEnvelope<ProjectRisk>>(`/projects/${projectId}/risk`, { auth: true }),
};
