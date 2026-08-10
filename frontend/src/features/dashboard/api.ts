import { apiRequest } from "@/shared/api/client";
import type {
  DashboardActivity,
  DashboardFindingsSummary,
  DashboardOverview,
  DashboardRiskTrend,
  DashboardTopAssets,
  DashboardUpcomingScans,
} from "@/shared/types/dashboard";

const base = "/organizations/current/dashboard";

export const dashboardApi = {
  getOverview: () => apiRequest<DashboardOverview>(`${base}/overview`, { auth: true }),

  getRiskTrend: () => apiRequest<DashboardRiskTrend>(`${base}/risk-trend`, { auth: true }),

  getFindingsSummary: (limit = 5) =>
    apiRequest<DashboardFindingsSummary>(`${base}/findings-summary?limit=${limit}`, {
      auth: true,
    }),

  getTopAssets: (limit = 5) =>
    apiRequest<DashboardTopAssets>(`${base}/top-assets?limit=${limit}`, { auth: true }),

  getActivity: (limit = 10) =>
    apiRequest<DashboardActivity>(`${base}/activity?limit=${limit}`, { auth: true }),

  getUpcomingScans: (limit = 10) =>
    apiRequest<DashboardUpcomingScans>(`${base}/upcoming-scans?limit=${limit}`, {
      auth: true,
    }),
};
