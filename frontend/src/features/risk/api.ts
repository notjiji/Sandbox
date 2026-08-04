import { apiRequest } from "@/shared/api/client";
import type { ProjectRisk } from "@/shared/types/risk";

export const riskApi = {
  getProjectRisk: (projectId: string) =>
    apiRequest<ProjectRisk>(`/projects/${projectId}/risk`, { auth: true }),
};
