import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Plus, Radar } from "lucide-react";
import AssetAskAiPanel from "@/features/ai/components/AssetAskAiPanel";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import EmptyState from "@/shared/components/EmptyState";
import { ListSkeleton } from "@/shared/components/ui/Skeleton";
import AssetPagination from "@/features/assets/components/AssetPagination";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";
import type { AssetSummary } from "@/shared/types/asset";
import type { ProjectSummary } from "@/shared/types/project";
import type { CreateScanRequest, ScanCompareData, ScanSummary, ScanType } from "@/shared/types/scan";
import { assetsApi } from "@/features/assets/api";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import ScanComparePanel from "../components/ScanComparePanel";
import AssetScanSchedulesPanel from "../components/AssetScanSchedulesPanel";
import ScanDetailPanel from "../components/ScanDetailPanel";
import ScanFilters, { filtersToQuery, type ScanFiltersState } from "../components/ScanFilters";
import ScanHistoryTable from "../components/ScanHistoryTable";
import { downloadScanReport, scansApi } from "../api";
import { profileLabel } from "../utils";

const PAGE_SIZE = 10;

interface ScanProfileOption {
  profile: ScanType;
  label: string;
  description: string;
  plugins: string[];
}

export default function Scans() {
  const { projectId, assetId } = useParams<{ projectId: string; assetId: string }>();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [asset, setAsset] = useState<AssetSummary | null>(null);
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [filters, setFilters] = useState<ScanFiltersState>({
    search: "",
    status: "",
    scan_type: "",
  });
  const [profiles, setProfiles] = useState<ScanProfileOption[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<ScanType>("full");
  const [selectedPlugins, setSelectedPlugins] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [actionId, setActionId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [detailScan, setDetailScan] = useState<ScanSummary | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [compareData, setCompareData] = useState<ScanCompareData | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);

  const customProfile = profiles.find((profile) => profile.profile === "custom");
  const availablePlugins = customProfile?.plugins ?? [];

  const loadScans = useCallback(async () => {
    if (!projectId || !assetId) return;
    const response = await scansApi.list(
      projectId,
      assetId,
      filtersToQuery(filters, page, limit),
    );
    setScans(response?.items ?? []);
    setTotal(response?.total ?? 0);
  }, [assetId, filters, limit, page, projectId]);

  const loadMeta = useCallback(async () => {
    if (!projectId || !assetId) return;
    const [projectResponse, assetResponse, profilesResponse] = await Promise.all([
      projectsApi.get(projectId),
      assetsApi.get(projectId, assetId),
      scansApi.profiles(projectId, assetId),
    ]);
    setProject(projectResponse ?? null);
    setAsset(assetResponse ?? null);
    setProfiles(profilesResponse?.items ?? []);
  }, [assetId, projectId]);

  const loadData = useCallback(async () => {
    await Promise.all([loadMeta(), loadScans()]);
  }, [loadMeta, loadScans]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      try {
        await loadData();
      } catch (error) {
        if (active) {
          toast.error(error instanceof ApiError ? error.message : "Unable to load scans.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [loadData]);

  const hasActiveScans = scans.some(
    (scan) => scan.status === "queued" || scan.status === "running",
  );

  useEffect(() => {
    if (!hasActiveScans) return undefined;

    const interval = setInterval(() => {
      loadScans().catch(() => {});
    }, 3000);

    return () => clearInterval(interval);
  }, [hasActiveScans, loadScans]);

  const handleFiltersChange = (next: ScanFiltersState) => {
    setFilters(next);
    setPage(1);
  };

  const toggleSelect = (scanId: string) => {
    setSelectedIds((current) => {
      if (current.includes(scanId)) {
        return current.filter((id) => id !== scanId);
      }
      if (current.length >= 2) {
        return [current[1]!, scanId];
      }
      return [...current, scanId];
    });
  };

  const openDetail = async (scan: ScanSummary) => {
    if (!projectId || !assetId) return;
    setDetailScan(scan);
    setDetailLoading(true);
    try {
      const full = await scansApi.get(projectId, assetId, scan.id);
      setDetailScan(full ?? scan);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to load scan details.");
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!projectId || !assetId || selectedIds.length !== 2) return;
    setCompareLoading(true);
    setCompareData(null);
    try {
      const result = await scansApi.compare(
        projectId,
        assetId,
        selectedIds[0]!,
        selectedIds[1]!,
      );
      setCompareData(result ?? null);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to compare scans.");
    } finally {
      setCompareLoading(false);
    }
  };

  const handleDownload = async (scanId: string) => {
    if (!projectId || !assetId) return;
    try {
      await downloadScanReport(projectId, assetId, scanId);
      toast.success("Scan report downloaded.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to download report.");
    }
  };

  const togglePlugin = (pluginName: string) => {
    setSelectedPlugins((current) =>
      current.includes(pluginName)
        ? current.filter((name) => name !== pluginName)
        : [...current, pluginName],
    );
  };

  const handleCreate = async () => {
    if (!projectId || !assetId) return;
    setCreating(true);
    try {
      const payload: CreateScanRequest = { scan_type: selectedProfile };
      if (selectedProfile === "custom") {
        if (selectedPlugins.length === 0) {
          toast.error("Select at least one plugin for a custom scan.");
          return;
        }
        payload.plugins = selectedPlugins;
      }
      await scansApi.create(projectId, assetId, payload);
      toast.success("Scan created.");
      setPage(1);
      await loadData();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to create scan.");
    } finally {
      setCreating(false);
    }
  };

  const handleRun = async (scanId: string) => {
    if (!projectId || !assetId) return;
    setActionId(scanId);
    try {
      await scansApi.run(projectId, assetId, scanId);
      toast.success("Scan started.");
      await loadScans();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to run scan.");
    } finally {
      setActionId(null);
    }
  };

  const handleCancel = async (scanId: string) => {
    if (!projectId || !assetId) return;
    setActionId(scanId);
    try {
      await scansApi.cancel(projectId, assetId, scanId);
      toast.success("Scan cancelled.");
      await loadScans();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to cancel scan.");
    } finally {
      setActionId(null);
    }
  };

  const activeProfile = profiles.find((profile) => profile.profile === selectedProfile);

  return (
    <DashboardShell
      title="Scans"
      subtitle={asset ? `Scan history for ${asset.name}` : "Asset scan history"}
    >
      <ProjectNav projectName={project?.name} assetName={asset?.name} active="scans" />

      {projectId && assetId && (
        <div className="mb-6">
          <AssetScanSchedulesPanel projectId={projectId} assetId={assetId} />
        </div>
      )}

      <div className="mb-4 space-y-4 rounded-lg border border-brand-800/50 p-4">
        <div>
          <p className="mb-2 text-sm font-medium text-brand-200">Scan profile</p>
          <div className="flex flex-wrap gap-2">
            {profiles.map((profile) => (
              <button
                key={profile.profile}
                type="button"
                onClick={() => setSelectedProfile(profile.profile)}
                className={`rounded-md border px-3 py-1.5 text-sm transition-colors ${
                  selectedProfile === profile.profile
                    ? "border-brand-400 bg-brand-800/60 text-brand-100"
                    : "border-brand-800/50 text-brand-400 hover:border-brand-700"
                }`}
              >
                {profile.label}
              </button>
            ))}
          </div>
          {activeProfile && (
            <p className="mt-2 text-sm text-brand-500">{activeProfile.description}</p>
          )}
        </div>

        {selectedProfile !== "custom" && activeProfile && (
          <div>
            <p className="mb-2 text-sm font-medium text-brand-200">Plugins</p>
            <div className="flex flex-wrap gap-2">
              {activeProfile.plugins.map((plugin) => (
                <span
                  key={plugin}
                  className="rounded-md border border-brand-800/50 px-2 py-1 text-xs uppercase tracking-wide text-brand-300"
                >
                  {plugin.replace("_", " ")}
                </span>
              ))}
            </div>
          </div>
        )}

        {selectedProfile === "custom" && (
          <div>
            <p className="mb-2 text-sm font-medium text-brand-200">Select plugins</p>
            <div className="flex flex-wrap gap-2">
              {availablePlugins.map((plugin) => {
                const selected = selectedPlugins.includes(plugin);
                return (
                  <button
                    key={plugin}
                    type="button"
                    onClick={() => togglePlugin(plugin)}
                    className={`rounded-md border px-3 py-1.5 text-xs uppercase tracking-wide transition-colors ${
                      selected
                        ? "border-brand-400 bg-brand-800/60 text-brand-100"
                        : "border-brand-800/50 text-brand-400 hover:border-brand-700"
                    }`}
                  >
                    {plugin.replace("_", " ")}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <button
          type="button"
          disabled={creating}
          onClick={handleCreate}
          className="btn-primary inline-flex items-center gap-2 text-sm"
        >
          <Plus size={16} />
          {creating ? "Creating..." : `New ${profileLabel(selectedProfile).toLowerCase()}`}
        </button>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-6"
      >
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-semibold text-brand-100">Scan history</h2>
          <p className="text-sm text-brand-500">
            {total} scan{total === 1 ? "" : "s"} total
          </p>
        </div>

        <ScanFilters filters={filters} onChange={handleFiltersChange} />

        <div className="mt-4">
          {loading ? (
            <ListSkeleton rows={5} />
          ) : scans.length === 0 ? (
            <EmptyState
              compact
              icon={Radar}
              title={
                filters.search || filters.status || filters.scan_type
                  ? "No matching scans"
                  : "No scans yet"
              }
              description={
                filters.search || filters.status || filters.scan_type
                  ? "Try adjusting your search or filters to find the scan you're looking for."
                  : "Run your first scan to assess this asset's security posture."
              }
            />
          ) : (
            <>
              <ScanHistoryTable
                scans={scans}
                selectedIds={selectedIds}
                actionId={actionId}
                onToggleSelect={toggleSelect}
                onOpen={openDetail}
                onRun={handleRun}
                onCancel={handleCancel}
                onDownload={handleDownload}
                onCompare={handleCompare}
              />
              <div className="mt-6">
                <AssetPagination
                  page={page}
                  limit={limit}
                  total={total}
                  pageSizeOptions={[10, 20, 50]}
                  onPageChange={setPage}
                  onLimitChange={(nextLimit) => {
                    setLimit(nextLimit);
                    setPage(1);
                  }}
                />
              </div>
            </>
          )}
        </div>
      </motion.div>

      <ScanDetailPanel
        scan={detailScan}
        loading={detailLoading}
        projectId={projectId ?? ""}
        assetId={assetId ?? ""}
        onClose={() => setDetailScan(null)}
        onDownload={handleDownload}
      />

      {(compareLoading || compareData) && (
        <ScanComparePanel
          data={compareData}
          loading={compareLoading}
          onClose={() => {
            setCompareData(null);
            setCompareLoading(false);
          }}
        />
      )}

      {asset && <AssetAskAiPanel assetName={asset.name} variant="compact" className="mt-6" />}
    </DashboardShell>
  );
}
