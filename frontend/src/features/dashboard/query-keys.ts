export const dashboardKeys = {
  all: ["dashboard"] as const,
  overview: () => [...dashboardKeys.all, "overview"] as const,
  riskTrend: () => [...dashboardKeys.all, "risk-trend"] as const,
  findingsSummary: () => [...dashboardKeys.all, "findings-summary"] as const,
  topAssets: () => [...dashboardKeys.all, "top-assets"] as const,
  activity: () => [...dashboardKeys.all, "activity"] as const,
  upcomingScans: () => [...dashboardKeys.all, "upcoming-scans"] as const,
};
