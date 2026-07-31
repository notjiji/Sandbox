import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Play, Radar, Square } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
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
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [scans, setScans] = useState([]);
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);

  const loadData = async () => {
    const [projectResponse, scansResponse] = await Promise.all([
      projectsApi.get(projectId),
      scansApi.list(projectId),
    ]);
    setProject(projectResponse?.data ?? null);
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
  }, [projectId]);

  const handleRun = async (scanId) => {
    setActionId(scanId);
    setAlert("");
    setSuccess("");
    try {
      await scansApi.run(projectId, scanId);
      setSuccess("Scan started.");
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
      await scansApi.cancel(projectId, scanId);
      setSuccess("Scan cancelled.");
      await loadData();
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to cancel scan.");
    } finally {
      setActionId(null);
    }
  };

  return (
    <DashboardShell title="Scans" subtitle="Monitor scan jobs for this project.">
      {alert && <FormAlert message={alert} />}
      {success && <FormAlert message={success} variant="success" />}
      <ProjectNav projectName={project?.name} active="scans" />

      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6">
        <h2 className="mb-4 text-lg font-semibold text-brand-100">Scan history</h2>
        {loading ? (
          <p className="text-brand-500">Loading...</p>
        ) : scans.length === 0 ? (
          <p className="text-brand-500">
            No scans yet. Create scans via the API once assets are registered for this project.
          </p>
        ) : (
          <ul className="space-y-3">
            {scans.map((scan) => (
              <li
                key={scan.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-brand-800/50 px-4 py-3"
              >
                <div>
                  <p className="font-medium text-brand-100">
                    {scan.scan_type} scan
                  </p>
                  <p className={`text-sm capitalize ${statusClass(scan.status)}`}>
                    {scan.status}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Radar size={18} className="text-brand-400" />
                  {scan.status === "pending" || scan.status === "queued" ? (
                    <button
                      type="button"
                      disabled={actionId === scan.id}
                      onClick={() => handleRun(scan.id)}
                      className="btn-primary inline-flex items-center gap-1 text-sm"
                    >
                      <Play size={14} />
                      Run
                    </button>
                  ) : null}
                  {scan.status === "running" ? (
                    <button
                      type="button"
                      disabled={actionId === scan.id}
                      onClick={() => handleCancel(scan.id)}
                      className="btn-ghost inline-flex items-center gap-1 text-sm"
                    >
                      <Square size={14} />
                      Cancel
                    </button>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </motion.div>
    </DashboardShell>
  );
}
