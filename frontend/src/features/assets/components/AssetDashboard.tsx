import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Bug,
  Database,
  FileText,
  Radar,
  ShieldAlert,
} from "lucide-react";
import StatCard, { SectionPanel } from "@/features/organizations/components/dashboard/StatCard";
import AssetRiskHistoryPanel from "./AssetRiskHistoryPanel";
import AssetAskAiPanel from "@/features/ai/components/AssetAskAiPanel";
import type { AssetOverview } from "@/shared/types/asset-overview";
import {
  formatActionLabel,
  formatRelativeTime,
  reportStatusClass,
  scanStatusClass,
} from "@/features/organizations/utils/format";
import PlaceholderPanel from "./PlaceholderPanel";
import { SCAN_STATUS_LABELS } from "../types";
import { formatDateTime, formatRiskScore } from "../utils";

interface AssetDashboardProps {
  overview: AssetOverview;
  projectId: string;
  assetId: string;
}

function severityClass(severity: string): string {
  switch (severity) {
    case "critical":
      return "text-red-300";
    case "high":
      return "text-orange-300";
    case "medium":
      return "text-yellow-200";
    case "low":
      return "text-brand-300";
    default:
      return "text-brand-400";
  }
}

export default function AssetDashboard({
  overview,
  projectId,
  assetId,
}: AssetDashboardProps) {
  const { asset, stats, risk, recent_scans, top_findings, recent_reports, recent_activity } =
    overview;

  const latestScan = recent_scans[0] ?? null;
  const riskScore = risk.scanned && risk.score != null ? risk.score : asset.current_risk_score;
  const riskGrade = risk.scanned && risk.grade ? risk.grade : asset.security_grade;

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel flex flex-col gap-6 p-6 lg:flex-row lg:items-center lg:justify-between"
      >
        <div className="flex items-start gap-4">
          <div className="rounded-xl border border-brand-700/50 bg-brand-950/40 p-3">
            <ShieldAlert size={28} className="text-brand-400" />
          </div>
          <div>
            <p className="text-sm text-brand-500">Risk score</p>
            <p className="text-4xl font-semibold tabular-nums text-brand-50">
              {formatRiskScore(riskScore ?? null)}
            </p>
            <p className="mt-1 text-sm text-brand-400">
              {risk.scanned ? "Based on latest scan" : "Run a scan to calculate risk"}
            </p>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-brand-800/50 px-4 py-3">
            <p className="text-xs text-brand-500">Grade</p>
            <p className="text-lg font-semibold text-brand-100">{riskGrade ?? "—"}</p>
          </div>
          <div className="rounded-lg border border-brand-800/50 px-4 py-3">
            <p className="text-xs text-brand-500">Latest scan</p>
            <p className="text-sm font-medium text-brand-100">
              {latestScan
                ? (SCAN_STATUS_LABELS[latestScan.status] ?? latestScan.status)
                : asset.last_scan_status
                  ? (SCAN_STATUS_LABELS[asset.last_scan_status] ?? asset.last_scan_status)
                  : "No scans"}
            </p>
            <p className="text-xs text-brand-500">
              {formatDateTime(latestScan?.lifecycle?.completed_at ?? asset.last_scan_at)}
            </p>
          </div>
          <div className="rounded-lg border border-brand-800/50 px-4 py-3">
            <p className="text-xs text-brand-500">Open findings</p>
            <p className="text-lg font-semibold text-brand-100">{stats.open_findings}</p>
          </div>
          <div className="rounded-lg border border-brand-800/50 px-4 py-3">
            <p className="text-xs text-brand-500">Critical</p>
            <p className="text-lg font-semibold text-red-300">{stats.critical_findings}</p>
          </div>
        </div>
      </motion.div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total scans"
          value={stats.scans}
          icon={Radar}
          href={`/projects/${projectId}/assets/${assetId}/scans`}
        />
        <StatCard
          label="Open findings"
          value={stats.open_findings}
          icon={Bug}
          accent={stats.open_findings > 0 ? "danger" : "default"}
          suffix={`${stats.total_findings} total`}
          href={`/projects/${projectId}/assets/${assetId}/findings`}
        />
        <StatCard
          label="Critical findings"
          value={stats.critical_findings}
          icon={AlertTriangle}
          accent={stats.critical_findings > 0 ? "danger" : "default"}
          href={`/projects/${projectId}/assets/${assetId}/findings`}
        />
        <StatCard
          label="Reports"
          value={stats.reports}
          icon={FileText}
          href={`/projects/${projectId}/assets/${assetId}/reports`}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <AssetRiskHistoryPanel projectId={projectId} assetId={assetId} />

        <SectionPanel
          title="Latest Scan"
          action={
            asset.status === "active" ? (
              <Link
                to={`/projects/${projectId}/assets/${assetId}/scans`}
                className="text-xs text-brand-400 hover:text-brand-200"
              >
                Run scan
              </Link>
            ) : undefined
          }
        >
          {!latestScan ? (
            <p className="text-sm text-brand-600">No scans yet. Run a scan to assess this asset.</p>
          ) : (
            <Link
              to={`/projects/${projectId}/assets/${assetId}/scans`}
              className="block rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-4 transition hover:border-brand-500/40"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm capitalize text-brand-100">{latestScan.scan_type} scan</p>
                  <p className="text-xs text-brand-600">
                    {formatRelativeTime(
                      latestScan.lifecycle?.completed_at ?? new Date().toISOString(),
                    )}
                  </p>
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs capitalize ${scanStatusClass(latestScan.status)}`}
                >
                  {latestScan.status}
                </span>
              </div>
              {(latestScan.plugin_runs?.length ?? 0) > 0 && (
                <p className="mt-3 text-xs text-brand-500">
                  {latestScan.plugin_runs!.length} plugin
                  {latestScan.plugin_runs!.length === 1 ? "" : "s"} executed
                </p>
              )}
            </Link>
          )}
        </SectionPanel>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionPanel
          title="Open Findings"
          action={
            <Link
              to={`/projects/${projectId}/findings`}
              className="text-xs text-brand-400 hover:text-brand-200"
            >
              View all
            </Link>
          }
        >
          {top_findings.length === 0 ? (
            <p className="text-sm text-brand-600">No open findings on this asset.</p>
          ) : (
            <ul className="space-y-3">
              {top_findings.map((finding) => (
                <li key={finding.id}>
                  <Link
                    to={`/projects/${projectId}/assets/${assetId}/findings`}
                    className="block rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3 transition hover:border-brand-500/40"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm text-brand-100">{finding.title}</p>
                        {finding.finding_code && (
                          <p className="text-xs text-brand-600">{finding.finding_code}</p>
                        )}
                      </div>
                      <span
                        className={`shrink-0 text-xs font-semibold uppercase ${severityClass(finding.severity)}`}
                      >
                        {finding.severity}
                      </span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </SectionPanel>

        <SectionPanel
          title="Recent Reports"
          action={
            <Link
              to={`/projects/${projectId}/assets/${assetId}/reports`}
              className="text-xs text-brand-400 hover:text-brand-200"
            >
              View all
            </Link>
          }
        >
          {recent_reports.length === 0 ? (
            <p className="text-sm text-brand-600">No reports yet.</p>
          ) : (
            <ul className="space-y-3">
              {recent_reports.map((report) => (
                <li key={report.id}>
                  <Link
                    to={`/projects/${projectId}/assets/${assetId}/reports`}
                    className="flex items-center justify-between gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3 transition hover:border-brand-500/40"
                  >
                    <div>
                      <p className="truncate text-sm text-brand-100">{report.name}</p>
                      <p className="text-xs text-brand-600">
                        {formatRelativeTime(report.created_at)}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs capitalize ${reportStatusClass(report.status)}`}
                    >
                      {report.status}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-xs text-brand-600">
            Reports are project-scoped and may include this asset.
          </p>
        </SectionPanel>
      </div>

      <SectionPanel
        title="Activity"
        action={
          <Link
            to={`/projects/${projectId}/settings?tab=activity`}
            className="text-xs text-brand-400 hover:text-brand-200"
          >
            Project activity
          </Link>
        }
      >
        {recent_activity.length === 0 ? (
          <p className="text-sm text-brand-600">No activity recorded for this asset yet.</p>
        ) : (
          <ul className="space-y-3">
            {recent_activity.map((entry) => (
              <li
                key={entry.id}
                className="flex items-start gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3"
              >
                <Database size={14} className="mt-0.5 shrink-0 text-brand-500" />
                <div>
                  <p className="text-sm text-brand-200">{formatActionLabel(entry.action)}</p>
                  <p className="text-xs text-brand-600">
                    {entry.resource_type ?? "system"} · {formatRelativeTime(entry.created_at)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </SectionPanel>

      <div className="grid gap-6 lg:grid-cols-3">
        <PlaceholderPanel
          title="Ports"
          description="Open port inventory from network scans will appear here."
        />
        <PlaceholderPanel
          title="Certificates"
          description="TLS certificate status and expiry tracking coming soon."
        />
        <PlaceholderPanel
          title="DNS"
          description="DNS records and resolution history will surface here after domain scans."
        />
      </div>

      <AssetAskAiPanel assetName={asset.name} />
    </div>
  );
}
