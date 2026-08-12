import { apiRequest } from "@/shared/api/client";
import type {
  EnrollmentResponse,
  MonitoringOverview,
  OrgMonitoringOverview,
} from "@/shared/types/monitoring";

const assetBase = (projectId: string, assetId: string) =>
  `/projects/${projectId}/assets/${assetId}/monitoring`;

export const monitoringApi = {
  getAssetOverview: (projectId: string, assetId: string, hours = 24) =>
    apiRequest<MonitoringOverview>(`${assetBase(projectId, assetId)}?hours=${hours}`, {
      auth: true,
    }),

  enroll: (projectId: string, assetId: string) =>
    apiRequest<EnrollmentResponse>(`${assetBase(projectId, assetId)}/enroll`, {
      method: "POST",
      auth: true,
    }),

  revoke: (projectId: string, assetId: string) =>
    apiRequest<{ message: string }>(`${assetBase(projectId, assetId)}/revoke`, {
      method: "POST",
      auth: true,
    }),

  getOrganizationOverview: () =>
    apiRequest<OrgMonitoringOverview>("/organizations/current/monitoring/overview", {
      auth: true,
    }),
};
