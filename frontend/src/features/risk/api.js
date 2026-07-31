import { apiRequest } from "@/shared/api/client";

export const riskApi = {
  getProjectRisk: (projectId) => apiRequest(`/projects/${projectId}/risk`, { auth: true }),
};
