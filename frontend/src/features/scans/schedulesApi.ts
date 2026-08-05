import { apiRequest } from "@/shared/api/client";
import type {
  ScanScheduleListData,
  ScanSchedulePreset,
  ScanScheduleSummary,
  UpdateScanScheduleRequest,
} from "@/shared/types/scan";

const base = (projectId: string, assetId: string) =>
  `/projects/${projectId}/assets/${assetId}/scan-schedules`;

export const scanSchedulesApi = {
  list: (projectId: string, assetId: string) =>
    apiRequest<ScanScheduleListData>(base(projectId, assetId), { auth: true }),

  update: (
    projectId: string,
    assetId: string,
    preset: ScanSchedulePreset,
    data: UpdateScanScheduleRequest,
  ) =>
    apiRequest<ScanScheduleSummary>(`${base(projectId, assetId)}/${preset}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),
};
