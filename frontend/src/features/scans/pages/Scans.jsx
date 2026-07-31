import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Play, Plus, Radar, Square } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import { assetsApi } from "@/features/assets/api";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import { scansApi } from "../api";

function statusClass(status) {
  switch (status) {
    case "completed":
      return "text-brand-300";
    case "running":
      return "text-yellow-400";
    case "failed":
      return "text-red-400";
    case "cancelled":
      return "text-brand-500";
    default:
      return "text-brand-400";
  }
}

export default function Scans() {
  const { projectId, assetId } = useParams();
  const [project, setProject] = useState(null);
  const [asset, setAsset] = useState(null);
  const [scans, setScans] = useState([]);
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [actionId, setActionId] = useState(null);

  const loadData = async () => {
    const [projectResponse, assetResponse, scansResponse] = await Promise.all([
      projectsApi.get(projectId),
      assetsApi.get(projectId, assetId),
      scansApi.list(projectId, assetId),
    ]);
    setProject(projectResponse?.data ?? null);
    setAsset(assetResponse?.data ?? null);
    setScans(scansResponse?.data?.items ?? []);
  };

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        await loadData();
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load scans.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [projectId, assetId]);

  const handleCreate = async () => {
    setCreating(true);
    setAlert("");
    setSuccess("");
    try {
      await scansApi.create(projectId, assetId, { scan_type: "full" });
      setSuccess("Scan created.");
      await loadData();
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to create scan.");
    } finally {
      setCreating(false);
    }
  };

  const handleRun = async (scanId) => {
    setActionId(scanId);
    setAlert("");
    setSuccess("");
    try {
      await scansApi.run(projectId, assetId, scanId);
      setSuccess("Scan completed.");
      await loadData();
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to run scan.");
    } finally {
      setActionId(null);
    }
  };

  const handleCancel = async (scanId) => {
    setActionId(scanId);
    setAlert("");
    setSuccess("");
    try {
      await scansApi.cancel(projectId, assetId, scanId);
      setSuccess("Scan cancelled.");
      await loadData();
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to cancel scan.");
    } finally {
      setActionId(null);
    }
  };

  return (
    <DashboardShell
      title="Scans"
      subtitle={asset ? `Scan history for ${asset.name}` : "Asset scan history"}
    >
      {alert && <FormAlert message={alert} />}
      {success && <FormAlert message={success} variant="success" />}
      <ProjectNav projectName={project?.name} assetName={asset?.name} active="scans" />

      <div className="mb-4">
        <button
          type="button"
          disabled={creating}
          onClick={handleCreate}
          className="btn-primary inline-flex items-center gap-2 text-sm"
        >
          <Plus size={16} />
          {creating ? "Creating..." : "New full scan"}
        </button>
      </div>

      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6">
        <h2 className="mb-4 text-lg font-semibold text-brand-100">Scan history</h2>
        {loading ? (
          <p className="text-brand-500">Loading...</p>
        ) : scans.length === 0 ? (
          <p className="text-brand-500">No scans yet. Create a scan to run plugins against this asset.</p>
        ) : (
          <ul className="space-y-3">
            {scans.map((scan) => (
              <li
                key={scan.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-brand-800/50 px-4 py-3"
              >
                <div>
                  <p className="font-medium text-brand-100">{scan.scan_type} scan</p>
                  <p className={`text-sm capitalize ${statusClass(scan.status)}`}>{scan.status}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Radar size={18} className="text-brand-400" />
                  {(scan.status === "pending" || scan.status === "failed") && (
                    <button
                      type="button"
                      disabled={actionId === scan.id}
                      onClick={() => handleRun(scan.id)}
                      className="btn-primary inline-flex items-center gap-1 text-sm"
                    >
                      <Play size={14} />
                      Run
                    </button>
                  )}
                  {scan.status === "running" && (
                    <button
                      type="button"
                      disabled={actionId === scan.id}
                      onClick={() => handleCancel(scan.id)}
                      className="btn-ghost inline-flex items-center gap-1 text-sm"
                    >
                      <Square size={14} />
                      Cancel
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </motion.div>
    </DashboardShell>
  );
}
