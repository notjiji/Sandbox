import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ChevronRight,
  FileText,
  FolderKanban,
  HardDrive,
  Layers,
  Radar,
  Shield,
  Users,
  Zap,
} from "lucide-react";
import DashboardShell from "../components/DashboardShell";
import SecurityScoreHero from "../components/dashboard/SecurityScoreHero";
import RiskTrendChart from "../components/dashboard/RiskTrendChart";
import StatCard, { SectionPanel } from "../components/dashboard/StatCard";
import { organizationsApi } from "../api";
import {
  formatRelativeTime,
  reportStatusClass,
  scanStatusClass,
} from "../utils/format";
import ActivityTimeline from "@/shared/components/activity/ActivityTimeline";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { OrganizationDetail } from "@/shared/types/organization";
import type { OrganizationOverview } from "@/shared/types/organization-overview";

export default function Dashboard() {
  const [organization, setOrganization] = useState<OrganizationDetail | null>(null);
  const [overview, setOverview] = useState<OrganizationOverview | null>(null);
  const [alert, setAlert] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [orgResponse, overviewResponse] = await Promise.all([
          organizationsApi.getCurrent(),
          organizationsApi.getOverview(),
        ]);
        if (!active) return;
        setOrganization(orgResponse ?? null);
        setOverview(overviewResponse ?? null);
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load dashboard.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  const stats = overview?.stats;
  const analytics = overview?.analytics;
  const security = overview?.security;
  const trends = analytics?.trends;
  const periodLabel = analytics?.period_days ?? 30;

  return (
    <DashboardShell
      title={organization?.name ?? "Organization"}
      subtitle="Security overview and workspace activity"
    >
      {alert && <FormAlert message={alert} />}

      {loading ? (
        <p className="text-brand-500">Loading organization dashboard...</p>
      ) : !overview || !security ? (
        <p className="text-brand-500">Dashboard data unavailable.</p>
      ) : (
        <div className="space-y-6">
          <SecurityScoreHero security={security} />

          <SectionPanel
            title="Analytics"
            action={
              <span className="text-xs text-brand-600">Last {periodLabel} days</span>
            }
          >
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
                <StatCard
                  label="Assets"
                  value={stats?.assets ?? 0}
                  icon={Layers}
                  href="/projects"
                  trend={
                    trends && trends.assets !== 0
                      ? { value: trends.assets, label: "Assets" }
                      : undefined
                  }
                />
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.04 }}
              >
                <StatCard
                  label="Members"
                  value={stats?.members ?? 0}
                  icon={Users}
                  href="/organization/members"
                  trend={
                    trends && trends.members !== 0
                      ? { value: trends.members, label: "Members" }
                      : undefined
                  }
                />
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.08 }}
              >
                <StatCard
                  label="Projects"
                  value={stats?.projects ?? 0}
                  icon={FolderKanban}
                  href="/projects"
                  trend={
                    trends && trends.projects !== 0
                      ? { value: trends.projects, label: "Projects" }
                      : undefined
                  }
                />
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.12 }}
              >
                <StatCard
                  label="Scans"
                  value={stats?.scans ?? 0}
                  icon={Radar}
                  href="/projects"
                  trend={
                    trends && trends.scans !== 0
                      ? { value: trends.scans, label: "Scans" }
                      : undefined
                  }
                />
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.16 }}
              >
                <StatCard
                  label="Reports"
                  value={stats?.reports ?? 0}
                  icon={FileText}
                  href="/projects"
                  trend={
                    trends && trends.reports !== 0
                      ? { value: trends.reports, label: "Reports" }
                      : undefined
                  }
                />
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <StatCard
                  label="Average Risk"
                  value={
                    analytics?.average_risk != null
                      ? Math.round(analytics.average_risk)
                      : "—"
                  }
                  icon={Shield}
                  accent={
                    analytics?.average_risk != null && analytics.average_risk >= 80
                      ? "default"
                      : analytics?.average_risk != null && analytics.average_risk >= 60
                        ? "warning"
                        : "danger"
                  }
                  trend={
                    trends?.average_risk != null && trends.average_risk !== 0
                      ? {
                          value: trends.average_risk,
                          label: "pts",
                          decimals: 1,
                        }
                      : undefined
                  }
                />
              </motion.div>
            </div>

            {trends && trends.critical_findings !== 0 && (
              <p className="mt-4 text-sm text-brand-400">
                <span
                  className={
                    trends.critical_findings < 0 ? "text-emerald-400" : "text-rose-400"
                  }
                >
                  {trends.critical_findings > 0 ? "+" : ""}
                  {trends.critical_findings} Critical Findings
                </span>
                <span className="text-brand-600"> · vs previous {periodLabel} days</span>
              </p>
            )}
          </SectionPanel>

          <div className="grid gap-6 lg:grid-cols-2">
            <SectionPanel
              title="Latest Scans"
              action={
                <Link to="/projects" className="text-xs text-brand-400 hover:text-brand-200">
                  View all
                </Link>
              }
            >
              {overview.recent_scans.length === 0 ? (
                <EmptyState message="No scans yet. Run a scan from any project asset." />
              ) : (
                <ul className="space-y-3">
                  {overview.recent_scans.map((scan) => (
                    <li key={scan.id}>
                      <Link
                        to={`/projects/${scan.project_id}/assets/${scan.asset_id}/scans`}
                        className="flex items-center justify-between gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3 transition hover:border-brand-500/40"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm text-brand-100">
                            {scan.scan_type} scan
                          </p>
                          <p className="text-xs text-brand-600">
                            {formatRelativeTime(scan.created_at)}
                          </p>
                        </div>
                        <span
                          className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs capitalize ${scanStatusClass(scan.status)}`}
                        >
                          {scan.status}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </SectionPanel>

            <SectionPanel title="Open Findings">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <FindingSeverityCard
                    label="Critical"
                    count={security.critical_findings}
                    tone="danger"
                  />
                  <FindingSeverityCard
                    label="High"
                    count={security.high_findings}
                    tone="warning"
                  />
                </div>
                {security.most_common_issue && (
                  <div className="rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3">
                    <p className="text-xs uppercase tracking-wider text-brand-600">
                      Most common issue
                    </p>
                    <p className="mt-1 text-sm text-brand-200">{security.most_common_issue}</p>
                  </div>
                )}
                {Object.keys(security.findings_by_plugin).length > 0 && (
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-wider text-brand-600">
                      By plugin
                    </p>
                    <ul className="space-y-2">
                      {Object.entries(security.findings_by_plugin)
                        .sort(([, a], [, b]) => b - a)
                        .slice(0, 4)
                        .map(([plugin, count]) => (
                          <li
                            key={plugin}
                            className="flex items-center justify-between text-sm text-brand-300"
                          >
                            <span className="truncate">{plugin}</span>
                            <span className="tabular-nums text-brand-500">{count}</span>
                          </li>
                        ))}
                    </ul>
                  </div>
                )}
              </div>
            </SectionPanel>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <SectionPanel
              title="Recent Reports"
              action={
                <Link to="/projects" className="text-xs text-brand-400 hover:text-brand-200">
                  View all
                </Link>
              }
            >
              {overview.recent_reports.length === 0 ? (
                <EmptyState message="No reports generated yet." />
              ) : (
                <ul className="space-y-3">
                  {overview.recent_reports.map((report) => (
                    <li key={report.id}>
                      <Link
                        to={`/projects/${report.project_id}/reports`}
                        className="flex items-center justify-between gap-3 rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-3 transition hover:border-brand-500/40"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm text-brand-100">{report.name}</p>
                          <p className="text-xs text-brand-600">
                            {formatRelativeTime(report.created_at)}
                          </p>
                        </div>
                        <span
                          className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs capitalize ${reportStatusClass(report.status)}`}
                        >
                          {report.status}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </SectionPanel>

            <SectionPanel
              title="Recent Activity"
              action={
                overview.recent_activity.length > 0 ? (
                  <Link
                    to="/organization/activity"
                    className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-200"
                  >
                    View all
                    <ChevronRight size={14} />
                  </Link>
                ) : undefined
              }
            >
              {overview.recent_activity.length === 0 ? (
                <EmptyState message="Activity will appear as your team works in this organization." />
              ) : (
                <ActivityTimeline items={overview.recent_activity} compact />
              )}
            </SectionPanel>
          </div>

          {security.risk_trend.length > 0 && (
            <SectionPanel title="Security Trend">
              <RiskTrendChart points={security.risk_trend} />
            </SectionPanel>
          )}

          <div className="grid gap-4 md:grid-cols-3">
            <UsageCard
              icon={HardDrive}
              label={overview.storage.label}
              value={overview.storage.value}
              available={overview.storage.available}
            />
            <UsageCard
              icon={Zap}
              label={overview.api_usage.label}
              value={overview.api_usage.value}
              available={overview.api_usage.available}
            />
            <UsageCard
              icon={ChevronRight}
              label={overview.subscription.label}
              value={overview.subscription.value}
              available={overview.subscription.available}
              muted
            />
          </div>
        </div>
      )}
    </DashboardShell>
  );
}

function EmptyState({ message }: { message: string }) {
  return <p className="text-sm text-brand-600">{message}</p>;
}

function FindingSeverityCard({
  label,
  count,
  tone,
}: {
  label: string;
  count: number;
  tone: "danger" | "warning";
}) {
  const toneClass = tone === "danger" ? "text-rose-400" : "text-amber-400";
  return (
    <div className="rounded-lg border border-brand-800/40 bg-void-200/20 px-4 py-4 text-center">
      <p className={`text-3xl font-semibold tabular-nums ${toneClass}`}>{count}</p>
      <p className="mt-1 text-xs text-brand-600">{label}</p>
    </div>
  );
}

function UsageCard({
  icon: Icon,
  label,
  value,
  available,
  muted = false,
}: {
  icon: typeof HardDrive;
  label: string;
  value: string;
  available: boolean;
  muted?: boolean;
}) {
  return (
    <div
      className={`glass-panel flex items-center gap-4 p-5 ${muted ? "opacity-70" : ""}`}
    >
      <div className="rounded-lg border border-brand-800/50 bg-void-200/30 p-3">
        <Icon size={18} className="text-brand-400" />
      </div>
      <div>
        <p className="text-sm text-brand-500">{label}</p>
        <p className="text-lg font-medium text-brand-100">{value}</p>
        {!available && (
          <p className="text-xs text-brand-600">Available in a future release</p>
        )}
      </div>
    </div>
  );
}
