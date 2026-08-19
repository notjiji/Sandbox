import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/features/dashboard/api";
import { dashboardKeys } from "@/features/dashboard/query-keys";

export function useDashboardOverview() {
  return useQuery({
    queryKey: dashboardKeys.overview(),
    queryFn: () => dashboardApi.getOverview(),
  });
}

export function useDashboardRiskTrend() {
  return useQuery({
    queryKey: dashboardKeys.riskTrend(),
    queryFn: () => dashboardApi.getRiskTrend(),
  });
}

export function useDashboardFindingsSummary() {
  return useQuery({
    queryKey: dashboardKeys.findingsSummary(),
    queryFn: () => dashboardApi.getFindingsSummary(),
  });
}

export function useDashboardTopAssets() {
  return useQuery({
    queryKey: dashboardKeys.topAssets(),
    queryFn: () => dashboardApi.getTopAssets(),
  });
}

export function useDashboardActivity() {
  return useQuery({
    queryKey: dashboardKeys.activity(),
    queryFn: () => dashboardApi.getActivity(),
  });
}

export function useDashboardUpcomingScans() {
  return useQuery({
    queryKey: dashboardKeys.upcomingScans(),
    queryFn: () => dashboardApi.getUpcomingScans(),
  });
}

export function useDashboardScanHistory(rangeDays: number) {
  return useQuery({
    queryKey: dashboardKeys.scanHistory(rangeDays),
    queryFn: () => dashboardApi.getScanHistory(rangeDays),
  });
}

export function useDashboardFindingTrend(rangeDays: number) {
  return useQuery({
    queryKey: dashboardKeys.findingTrend(rangeDays),
    queryFn: () => dashboardApi.getFindingTrend(rangeDays),
  });
}
