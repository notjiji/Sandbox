import { useCallback, useEffect, useState } from "react";
import { ArrowDown, CalendarClock } from "lucide-react";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";
import type { ScanSchedulePreset, ScanScheduleSummary } from "@/shared/types/scan";
import { scanSchedulesApi } from "../schedulesApi";

interface AssetScanSchedulesPanelProps {
  projectId: string;
  assetId: string;
}

function formatScheduleTime(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function AssetScanSchedulesPanel({
  projectId,
  assetId,
}: AssetScanSchedulesPanelProps) {
  const [schedules, setSchedules] = useState<ScanScheduleSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingPreset, setUpdatingPreset] = useState<ScanSchedulePreset | null>(null);

  const loadSchedules = useCallback(async () => {
    const response = await scanSchedulesApi.list(projectId, assetId);
    setSchedules(response?.items ?? []);
  }, [assetId, projectId]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      try {
        await loadSchedules();
      } catch (error) {
        if (active) {
          toast.error(
            error instanceof ApiError ? error.message : "Unable to load scan schedules.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [loadSchedules]);

  const handleToggle = async (schedule: ScanScheduleSummary) => {
    setUpdatingPreset(schedule.preset);
    try {
      const updated = await scanSchedulesApi.update(projectId, assetId, schedule.preset, {
        enabled: !schedule.enabled,
      });
      if (updated) {
        setSchedules((current) =>
          current.map((item) => (item.preset === updated.preset ? updated : item)),
        );
        toast.success(
          updated.enabled
            ? `${updated.label} schedule enabled.`
            : `${updated.label} schedule disabled.`,
        );
      }
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to update schedule.");
    } finally {
      setUpdatingPreset(null);
    }
  };

  return (
    <div className="glass-panel p-6">
      <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-brand-600/40 bg-brand-900/30 p-2.5 text-brand-300">
            <CalendarClock size={20} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-brand-100">Scan schedules</h2>
            <p className="text-sm text-brand-500">Per-asset recurring scans — not a global scheduler.</p>
          </div>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-brand-500">Loading schedules...</p>
      ) : (
        <div className="space-y-0">
          {schedules.map((schedule, index) => (
            <div key={schedule.preset}>
              <div className="rounded-lg border border-brand-800/50 bg-void-200/20 px-4 py-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-medium text-brand-100">{schedule.label}</p>
                      <span className="rounded-full border border-brand-700/50 bg-brand-900/40 px-2 py-0.5 text-xs text-brand-400">
                        {schedule.cadence}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-brand-500">
                      Profile: {schedule.profile_label}
                    </p>
                    <div className="mt-3 grid gap-2 text-xs text-brand-500 sm:grid-cols-2">
                      <p>
                        Last run:{" "}
                        <span className="text-brand-300">{formatScheduleTime(schedule.last_run_at)}</span>
                      </p>
                      <p>
                        Next run:{" "}
                        <span className="text-brand-300">
                          {schedule.enabled ? formatScheduleTime(schedule.next_run_at) : "—"}
                        </span>
                      </p>
                    </div>
                  </div>

                  <label className="inline-flex shrink-0 cursor-pointer items-center gap-3">
                    <span className="text-sm text-brand-400">
                      {schedule.enabled ? "Enabled" : "Disabled"}
                    </span>
                    <button
                      type="button"
                      role="switch"
                      aria-checked={schedule.enabled}
                      disabled={updatingPreset === schedule.preset}
                      onClick={() => handleToggle(schedule)}
                      className={`relative h-7 w-12 rounded-full transition ${
                        schedule.enabled ? "bg-brand-500" : "bg-brand-800"
                      } ${updatingPreset === schedule.preset ? "opacity-60" : ""}`}
                    >
                      <span
                        className={`absolute top-0.5 h-6 w-6 rounded-full bg-brand-50 transition ${
                          schedule.enabled ? "left-5" : "left-0.5"
                        }`}
                      />
                    </button>
                  </label>
                </div>
              </div>
              {index < schedules.length - 1 && (
                <div className="flex justify-center py-1 text-brand-700" aria-hidden>
                  <ArrowDown size={14} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
