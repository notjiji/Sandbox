import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Download } from "lucide-react";
import DashboardShell from "../components/DashboardShell";
import Pagination from "@/shared/components/Pagination";
import ActivityTimeline from "@/shared/components/activity/ActivityTimeline";
import EmptyState from "@/shared/components/EmptyState";
import { ListSkeleton } from "@/shared/components/ui/Skeleton";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";
import type { ActivityEvent, ActivityFilters } from "@/shared/types/activity";
import { organizationsApi } from "../api";
import { auditApi } from "../audit-api";

const PAGE_SIZE = 20;

const ACTION_OPTIONS = [
  { value: "", label: "All actions" },
  { value: "asset.create", label: "Asset created" },
  { value: "asset.update", label: "Asset updated" },
  { value: "asset.delete", label: "Asset deleted" },
  { value: "scan.started", label: "Scan started" },
  { value: "scan.completed", label: "Scan completed" },
  { value: "scan.failed", label: "Scan failed" },
  { value: "scan.plugin_failed", label: "Plugin failed" },
  { value: "report.generate", label: "Report generated" },
  { value: "report.download", label: "Report downloaded" },
  { value: "org.member_invite", label: "Member invited" },
  { value: "org.member_remove", label: "Member removed" },
  { value: "org.config_changed", label: "Configuration changed" },
  { value: "ai.summary_generated", label: "AI summary generated" },
] as const;

const SEVERITY_OPTIONS = [
  { value: "", label: "All severities" },
  { value: "info", label: "Info" },
  { value: "warning", label: "Warning" },
  { value: "error", label: "Error" },
  { value: "critical", label: "Critical" },
] as const;

const EMPTY_FILTERS: ActivityFilters = {
  action: "",
  actor: "",
  severity: "",
  date_from: "",
  date_to: "",
};

function hasActiveFilters(filters: ActivityFilters): boolean {
  return Boolean(
    filters.action || filters.actor || filters.severity || filters.date_from || filters.date_to,
  );
}

export default function OrganizationActivity() {
  const [items, setItems] = useState<ActivityEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<ActivityFilters>(EMPTY_FILTERS);
  const [loading, setLoading] = useState(true);

  const [exporting, setExporting] = useState(false);

  const setFilter = <K extends keyof ActivityFilters>(key: K, value: ActivityFilters[K]) => {
    setPage(1);
    setFilters((current) => ({ ...current, [key]: value }));
  };

  const handleExport = async (format: "csv" | "pdf") => {
    setExporting(true);
    try {
      if (format === "pdf") {
        await auditApi.exportPdf(filters);
      } else {
        await auditApi.exportCsv(filters);
      }
      toast.success(format === "pdf" ? "Audit log PDF downloaded." : "Audit log CSV downloaded.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to export audit logs.");
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      try {
        const data = await organizationsApi.getActivity(page, PAGE_SIZE, filters);
        if (!active) return;
        setItems(data?.items ?? []);
        setTotal(data?.total ?? 0);
      } catch (error) {
        if (active) {
          toast.error(error instanceof ApiError ? error.message : "Unable to load activity.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [page, filters]);

  return (
    <DashboardShell
      title="Activity"
      subtitle="Human-friendly timeline of what happened in your organization."
    >
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-6"
      >
        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-brand-700/50 bg-brand-950/50">
              <Activity size={18} className="text-brand-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-brand-100">Organization timeline</h2>
              <p className="text-sm text-brand-500">
                Invites, assets, scans, reports, and security changes — not forensic audit logs.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="btn-ghost inline-flex items-center gap-2 text-sm disabled:opacity-60"
              disabled={exporting}
              onClick={() => void handleExport("csv")}
            >
              <Download size={14} />
              CSV
            </button>
            <button
              type="button"
              className="btn-ghost inline-flex items-center gap-2 text-sm disabled:opacity-60"
              disabled={exporting}
              onClick={() => void handleExport("pdf")}
            >
              <Download size={14} />
              PDF
            </button>
          </div>
        </div>

        <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <input
            type="search"
            value={filters.actor ?? ""}
            onChange={(event) => setFilter("actor", event.target.value)}
            className="input-field"
            placeholder="Person (e.g. Amine)"
            aria-label="Filter by person"
          />
          <select
            value={filters.action ?? ""}
            onChange={(event) => setFilter("action", event.target.value)}
            className="input-field"
            aria-label="Filter by action"
          >
            {ACTION_OPTIONS.map((option) => (
              <option key={option.value || "all"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <select
            value={filters.severity ?? ""}
            onChange={(event) => setFilter("severity", event.target.value)}
            className="input-field"
            aria-label="Filter by severity"
          >
            {SEVERITY_OPTIONS.map((option) => (
              <option key={option.value || "all"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={filters.date_from ?? ""}
            onChange={(event) => setFilter("date_from", event.target.value)}
            className="input-field"
            aria-label="From date"
          />
          <input
            type="date"
            value={filters.date_to ?? ""}
            onChange={(event) => setFilter("date_to", event.target.value)}
            className="input-field"
            aria-label="To date"
          />
        </div>

        {loading ? (
          <ListSkeleton rows={5} />
        ) : items.length === 0 ? (
          <EmptyState
            compact
            icon={Activity}
            title={hasActiveFilters(filters) ? "No matching activity" : "No activity yet"}
            description={
              hasActiveFilters(filters)
                ? "Try a different date range, action, person, or severity."
                : "Activity will appear as your team works in this organization."
            }
          />
        ) : (
          <>
            <ActivityTimeline items={items} />
            <div className="mt-8 border-t border-brand-800/40 pt-6">
              <Pagination page={page} limit={PAGE_SIZE} total={total} onPageChange={setPage} />
            </div>
          </>
        )}
      </motion.div>
    </DashboardShell>
  );
}
