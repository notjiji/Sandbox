import { apiRequest, refreshAccessToken } from "@/shared/api/client";
import { orgStorage } from "@/features/organizations/storage";
import { tokenStorage } from "@/features/auth/storage";
import type { ActivityFilters } from "@/shared/types/activity";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

function toQuery(filters?: ActivityFilters, extra?: Record<string, string>): string {
  const params = new URLSearchParams();
  if (filters) {
    const entries: Array<[string, string | undefined]> = [
      ["action", filters.action],
      ["actor", filters.actor],
      ["asset_id", filters.asset_id],
      ["severity", filters.severity],
      ["date_from", filters.date_from],
      ["date_to", filters.date_to],
    ];
    for (const [key, value] of entries) {
      if (value?.trim()) params.set(key, value.trim());
    }
  }
  if (extra) {
    for (const [key, value] of Object.entries(extra)) {
      if (value) params.set(key, value);
    }
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

async function downloadExport(path: string, filename: string): Promise<void> {
  const headers: Record<string, string> = {};
  const accessToken = tokenStorage.getAccessToken();
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  const orgId = orgStorage.getActiveOrgId();
  if (orgId) headers["X-Organization-ID"] = orgId;

  let response = await fetch(`${API_BASE_URL}${path}`, { credentials: "include", headers });
  if (response.status === 401 && tokenStorage.getRefreshToken()) {
    await refreshAccessToken();
    const refreshed = tokenStorage.getAccessToken();
    if (refreshed) headers.Authorization = `Bearer ${refreshed}`;
    response = await fetch(`${API_BASE_URL}${path}`, { credentials: "include", headers });
  }
  if (!response.ok) {
    throw new Error("Unable to export audit logs.");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export const auditApi = {
  exportCsv: (filters?: ActivityFilters) =>
    downloadExport(`/audit-logs/export${toQuery(filters, { format: "csv" })}`, "audit-logs.csv"),

  exportPdf: (filters?: ActivityFilters) =>
    downloadExport(`/audit-logs/export${toQuery(filters, { format: "pdf" })}`, "audit-logs.pdf"),

  integrity: () =>
    apiRequest<{ valid: boolean; checked: number; broken_at: string | null; reason: string | null }>(
      "/audit-logs/integrity",
      { auth: true },
    ),
};
