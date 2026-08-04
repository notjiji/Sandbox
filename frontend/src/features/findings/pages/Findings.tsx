import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Bug } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { FindingSeverity, FindingSummary } from "@/shared/types/finding";
import type { ProjectSummary } from "@/shared/types/project";
import { projectsApi } from "@/features/projects/api";
import ProjectNav from "@/features/projects/components/ProjectNav";
import { findingsApi } from "../api";

interface FindingWithDescription extends FindingSummary {
  description?: string | null;
}

function severityClass(severity: FindingSeverity | string): string {
  switch (severity) {
    case "critical":
      return "text-red-400";
    case "high":
      return "text-orange-400";
    case "medium":
      return "text-yellow-400";
    case "low":
      return "text-brand-300";
    default:
      return "text-brand-400";
  }
}

export default function Findings() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [findings, setFindings] = useState<FindingWithDescription[]>([]);
  const [alert, setAlert] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    if (!projectId) return undefined;

    async function load() {
      if (!projectId) return;
      try {
        const [projectResponse, findingsResponse] = await Promise.all([
          projectsApi.get(projectId),
          findingsApi.list(projectId),
        ]);
        if (!active) return;
        setProject(projectResponse ?? null);
        setFindings((findingsResponse?.items ?? []) as FindingWithDescription[]);
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load findings.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [projectId]);

  return (
    <DashboardShell title="Findings" subtitle="Vulnerabilities discovered in this project.">
      {alert && <FormAlert message={alert} />}
      <ProjectNav projectName={project?.name} active="findings" />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-6"
      >
        <h2 className="mb-4 text-lg font-semibold text-brand-100">All findings</h2>
        {loading ? (
          <p className="text-brand-500">Loading...</p>
        ) : findings.length === 0 ? (
          <p className="text-brand-500">No findings yet. Run a scan to populate results.</p>
        ) : (
          <ul className="space-y-3">
            {findings.map((finding) => (
              <li
                key={finding.id}
                className="flex items-start justify-between gap-4 rounded-lg border border-brand-800/50 px-4 py-3"
              >
                <div>
                  <p className="font-medium text-brand-100">{finding.title}</p>
                  {finding.description && (
                    <p className="mt-1 text-sm text-brand-500">{finding.description}</p>
                  )}
                  <p className="mt-2 text-xs uppercase tracking-wide text-brand-600">
                    {finding.status}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span
                    className={`text-sm font-semibold uppercase ${severityClass(finding.severity)}`}
                  >
                    {finding.severity}
                  </span>
                  <Bug size={18} className="text-brand-400" />
                </div>
              </li>
            ))}
          </ul>
        )}
      </motion.div>
    </DashboardShell>
  );
}
