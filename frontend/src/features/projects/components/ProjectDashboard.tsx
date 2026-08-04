import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Bug,
  Database,
  FileText,
  Globe,
  Radar,
  ShieldAlert,
} from "lucide-react";
import StatCard, { SectionPanel } from "@/features/organizations/components/dashboard/StatCard";
import AiSummaryPanel from "@/shared/components/AiSummaryPanel";
import type { OrganizationDetail } from "@/shared/types/organization";
import {
  formatActionLabel,
  formatRelativeTime,
  reportStatusClass,
  scanStatusClass,
} from "@/features/organizations/utils/format";
import type { ProjectOverview } from "@/shared/types/project-overview";

interface ProjectDashboardProps {
  overview: ProjectOverview;
  projectId: string;
  organization?: OrganizationDetail | null;
}

export default function ProjectDashboard({ overview, projectId, organization }: ProjectDashboardProps) {
  const { stats, security, recent_scans, recent_reports, recent_activity, ai_summary } =
    overview;

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel flex flex-wrap items-center justify-between gap-4 p-6"
      >
        <div className="flex items-center gap-3">
          <ShieldAlert size={24} className="text-brand-400" />
          <div>
            <p className="text-sm text-brand-500">Security score</p>
            <p className="text-3xl font-semibold text-brand-100">
              {security.security_score.toFixed(1)}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-6 text-sm text-brand-500">
          <span>
            Grade <strong className="text-brand-200">{security.grade}</strong>
          </span>
          <span>
            Risk <strong className="capitalize text-brand-200">{security.risk_level}</strong>
          </span>
          <span>
            Open findings{" "}
            <strong className="text-brand-200">{security.open_findings}</strong>
          </span>
        </div>
      </motion.div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Assets"
          value={stats.assets}
          icon={Globe}
          href={`/projects/${projectId}/assets`}
        />
        <StatCard
          label="Scans"
          value={stats.scans}
          icon={Radar}
          href={`/projects/${projectId}/assets`}
        />
        <StatCard
          label="Open findings"
          value={stats.open_findings}
          icon={Bug}
          accent={stats.open_findings > 0 ? "danger" : "default"}
          suffix={`${stats.total_findings} total`}
          href={`/projects/${projectId}/findings`}
        />
        <StatCard
          label="Reports"
          value={stats.reports}
          icon={FileText}
          href={`/projects/${projectId}/reports`}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionPanel
          title="Latest Scans"
          action={
            <Link
              to={`/projects/${projectId}/assets`}
              className="text-xs text-brand-400 hover:text-brand-200"
            >
              View assets
            </Link>
          }
        >
          {recent_scans.length === 0 ? (
            <p className="text-sm text-brand-600">No scans yet.</p>
          ) : (
            <ul className="space-y-3">
              {recent_scans.map((scan) => (
                <li key={scan.id}>
                  <Link
                    to={`/projects/${projectId}/assets/${scan.asset_id}/scans`}
                    className="flex items-center justify-between gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3 transition hover:border-brand-500/40"
                  >
                    <div>
                      <p className="text-sm capitalize text-brand-100">{scan.scan_type} scan</p>
                      <p className="text-xs text-brand-600">
                        {formatRelativeTime(scan.created_at)}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs capitalize ${scanStatusClass(scan.status)}`}
                    >
                      {scan.status}
                    </span>
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
              to={`/projects/${projectId}/reports`}
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
                    to={`/projects/${projectId}/reports`}
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
        </SectionPanel>
      </div>

      <SectionPanel
        title="Recent Activity"
        action={
          <Link
            to={`/projects/${projectId}/settings?tab=activity`}
            className="text-xs text-brand-400 hover:text-brand-200"
          >
            View all
          </Link>
        }
      >
        {recent_activity.length === 0 ? (
          <p className="text-sm text-brand-600">No project activity yet.</p>
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

      <AiSummaryPanel
        organizationName={organization?.name ?? "Organization"}
        logoUrl={organization?.logo_url}
        label={ai_summary.label}
        value={ai_summary.value}
        className="opacity-90"
      />
    </div>
  );
}
