export const monitoringKeys = {
  all: ["monitoring"] as const,
  asset: (projectId: string, assetId: string, hours = 24) =>
    [...monitoringKeys.all, "asset", projectId, assetId, hours] as const,
  organization: () => [...monitoringKeys.all, "organization"] as const,
};
