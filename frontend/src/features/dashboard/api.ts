import { apiRequest } from "@/shared/api/client";
import type {
  DashboardActivity,
  DashboardFindingsSummary,
  DashboardFindingTrend,
  DashboardOverview,
  DashboardRiskTrend,
  DashboardScanHistory,
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

  getScanHistory: (rangeDays = 30, limit = 25) =>
    apiRequest<DashboardScanHistory>(
      `${base}/scan-history?range_days=${rangeDays}&limit=${limit}`,
      { auth: true },
    ),

  getFindingTrend: (rangeDays = 30) =>
    apiRequest<DashboardFindingTrend>(`${base}/finding-trend?range_days=${rangeDays}`, {
      auth: true,
    }),
};
