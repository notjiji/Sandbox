import { useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import DashboardShell from "../components/DashboardShell";
import DashboardHeader from "../components/dashboard/DashboardHeader";
import DashboardEmptyState from "../components/dashboard/DashboardEmptyState";
import DashboardSkeleton from "../components/dashboard/DashboardSkeleton";
import SecurityScorePanel from "../components/dashboard/SecurityScorePanel";
import RiskTrendChart from "../components/dashboard/RiskTrendChart";
import FindingsSummaryChart from "../components/dashboard/FindingsSummaryChart";
import AssetOverviewChart from "../components/dashboard/AssetOverviewChart";
import CriticalFindingsList from "../components/dashboard/CriticalFindingsList";
import TopRiskyAssets from "../components/dashboard/TopRiskyAssets";
import UpcomingScansPanel from "../components/dashboard/UpcomingScansPanel";
import ServerHealthPanel from "@/features/monitoring/components/ServerHealthPanel";
import { SectionPanel } from "../components/dashboard/StatCard";
import {
  useDashboardActivity,
  useDashboardFindingsSummary,
  useDashboardOverview,
  useDashboardRiskTrend,
  useDashboardTopAssets,
  useDashboardUpcomingScans,
} from "@/features/dashboard/hooks/useSecurityDashboard";
import ActivityTimeline from "@/shared/components/activity/ActivityTimeline";
import ErrorState from "@/shared/components/ErrorState";
import { PanelSkeleton } from "@/shared/components/ui/Skeleton";
import { useOrganizationRole } from "@/shared/hooks/useOrganizationRole";
import { useQueryClient } from "@tanstack/react-query";
import { dashboardKeys } from "@/features/dashboard/query-keys";
import GenerateReportModal from "@/features/reports/components/GenerateReportModal";

export default function Dashboard() {
  const queryClient = useQueryClient();
  const { canRunScan, canGenerateReport } = useOrganizationRole();
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const overviewQuery = useDashboardOverview();
  const riskTrendQuery = useDashboardRiskTrend();
  const findingsQuery = useDashboardFindingsSummary();
  const topAssetsQuery = useDashboardTopAssets();
  const activityQuery = useDashboardActivity();
  const upcomingQuery = useDashboardUpcomingScans();

  const retryAll = () => {
    void queryClient.invalidateQueries({ queryKey: dashboardKeys.all });
  };

  if (overviewQuery.isLoading) {
    return (
      <DashboardShell title="Security Intelligence" subtitle="Organization security posture">
        <DashboardSkeleton />
      </DashboardShell>
    );
  }

  if (overviewQuery.isError || !overviewQuery.data) {
    return (
      <DashboardShell title="Security Intelligence" subtitle="Organization security posture">
        <ErrorState
          title="Unable to load security data"
          description={
            <>
              Something went wrong while retrieving your organization&apos;s security posture.
            </>
          }
          onRetry={retryAll}
          retryLabel="Retry"
        />
      </DashboardShell>
    );
  }

  const overview = overviewQuery.data;
  const projectId = overview.primary_project_id;
  const assetsHref = projectId ? `/projects/${projectId}/assets` : "/projects";
  const findingsHref = projectId ? `/projects/${projectId}/findings?severity=critical` : "/projects";
  const lastScanHref =
    overview.last_scan.project_id && overview.last_scan.asset_id
      ? `/projects/${overview.last_scan.project_id}/assets/${overview.last_scan.asset_id}/scans`
      : undefined;
  const isEmpty =
    overview.assets.total === 0 &&
    !overview.last_scan.timestamp &&
    overview.scanned_assets === 0;

  if (isEmpty) {
    return (
      <DashboardShell title="Security Intelligence" subtitle="Organization security posture">
        <DashboardEmptyState primaryProjectId={projectId} canRunScan={canRunScan} />
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title="Security Intelligence" subtitle="Organization security posture">
      <div className="space-y-6">
        <DashboardHeader
          lastScan={overview.last_scan}
          canRunScan={canRunScan}
          canGenerateReport={canGenerateReport}
          primaryProjectId={projectId}
          onGenerateReport={() => setReportModalOpen(true)}
        />

        <SecurityScorePanel
          overview={overview}
          assetsHref={assetsHref}
          findingsHref={findingsHref}
          lastScanHref={lastScanHref}
        />

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <SectionPanel title="Risk Trend">
            {riskTrendQuery.isLoading ? (
              <PanelSkeleton lines={3} />
            ) : riskTrendQuery.isError ? (
              <ErrorState compact onRetry={() => void riskTrendQuery.refetch()} />
            ) : (
              <RiskTrendChart points={riskTrendQuery.data?.history ?? []} />
            )}
          </SectionPanel>

          <SectionPanel title="Findings by Severity">
            {findingsQuery.isLoading ? (
              <PanelSkeleton lines={4} />
            ) : findingsQuery.isError ? (
              <ErrorState compact onRetry={() => void findingsQuery.refetch()} />
            ) : (
              <FindingsSummaryChart
                breakdown={findingsQuery.data?.breakdown ?? overview.findings}
                projectId={projectId}
              />
            )}
          </SectionPanel>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <SectionPanel
            title="Critical Findings"
            action={
              <Link to={findingsHref} className="text-xs text-brand-400 hover:text-brand-200">
                View all
              </Link>
            }
          >
            {findingsQuery.isLoading ? (
              <PanelSkeleton lines={4} />
            ) : findingsQuery.isError ? (
              <ErrorState compact onRetry={() => void findingsQuery.refetch()} />
            ) : (
              <CriticalFindingsList
                findings={findingsQuery.data?.top_findings ?? []}
                projectId={projectId}
              />
            )}
          </SectionPanel>

          <SectionPanel title="Asset Security" action={<Link to={assetsHref} className="text-xs text-brand-400 hover:text-brand-200">View assets</Link>}>
            <AssetOverviewChart assets={overview.assets} href={assetsHref} />
          </SectionPanel>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <SectionPanel title="Highest Risk Assets">
            {topAssetsQuery.isLoading ? (
              <PanelSkeleton lines={4} />
            ) : topAssetsQuery.isError ? (
              <ErrorState compact onRetry={() => void topAssetsQuery.refetch()} />
            ) : (
              <TopRiskyAssets assets={topAssetsQuery.data?.items ?? []} />
            )}
          </SectionPanel>

          <SectionPanel
            title="Upcoming Scans"
            action={
              projectId ? (
                <Link
                  to={`/projects/${projectId}/assets`}
                  className="text-xs text-brand-400 hover:text-brand-200"
                >
                  View scans
                </Link>
              ) : undefined
            }
          >
            {upcomingQuery.isLoading ? (
              <PanelSkeleton lines={4} />
            ) : upcomingQuery.isError ? (
              <ErrorState compact onRetry={() => void upcomingQuery.refetch()} />
            ) : (
              <UpcomingScansPanel scans={upcomingQuery.data?.items ?? []} />
            )}
          </SectionPanel>
        </div>

        <SectionPanel title="Server health">
          <ServerHealthPanel />
        </SectionPanel>

        <SectionPanel
          title="Recent Activity"
          action={
            <Link
              to="/organization/activity"
              className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-200"
            >
              View all
              <ChevronRight size={14} />
            </Link>
          }
        >
          {activityQuery.isLoading ? (
            <PanelSkeleton lines={4} />
          ) : activityQuery.isError ? (
            <ErrorState compact onRetry={() => void activityQuery.refetch()} />
          ) : (activityQuery.data?.items.length ?? 0) === 0 ? (
            <p className="text-sm text-brand-600">Activity will appear as your team works.</p>
          ) : (
            <ActivityTimeline items={activityQuery.data?.items ?? []} compact />
          )}
        </SectionPanel>
      </div>

      {projectId && (
        <GenerateReportModal
          open={reportModalOpen}
          onClose={() => setReportModalOpen(false)}
          projectId={projectId}
        />
      )}
    </DashboardShell>
  );
}
