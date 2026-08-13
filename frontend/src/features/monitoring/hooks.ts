import { useQuery } from "@tanstack/react-query";
import { monitoringApi } from "./api";
import { monitoringKeys } from "./query-keys";

export function useAssetMonitoring(projectId?: string, assetId?: string, hours = 24) {
  return useQuery({
    queryKey: monitoringKeys.asset(projectId ?? "", assetId ?? "", hours),
    queryFn: () => monitoringApi.getAssetOverview(projectId!, assetId!, hours),
    enabled: Boolean(projectId && assetId),
    refetchInterval: 15_000,
  });
}

export function useOrganizationMonitoring() {
  return useQuery({
    queryKey: monitoringKeys.organization(),
    queryFn: () => monitoringApi.getOrganizationOverview(),
    refetchInterval: 30_000,
  });
}
