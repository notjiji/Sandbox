import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Bug } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import EmptyState from "@/shared/components/EmptyState";
import ListSearchBar from "@/shared/components/ListSearchBar";
import { ListSkeleton } from "@/shared/components/ui/Skeleton";
import { toast } from "@/shared/lib/toast";
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
  const [searchParams, setSearchParams] = useSearchParams();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [findings, setFindings] = useState<FindingWithDescription[]>([]);
  const [search, setSearch] = useState("");
  const severity = searchParams.get("severity") ?? "";
  const [loading, setLoading] = useState(true);

  const setSeverity = (value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set("severity", value);
    else next.delete("severity");
    setSearchParams(next, { replace: true });
  };

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
          toast.error(error instanceof ApiError ? error.message : "Unable to load findings.");
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

  const filteredFindings = useMemo(() => {
    return findings.filter((finding) => {
      if (severity && finding.severity !== severity) return false;
      if (!search.trim()) return true;
      const needle = search.toLowerCase();
      return (
        finding.title.toLowerCase().includes(needle) ||
        (finding.description?.toLowerCase().includes(needle) ?? false) ||
        finding.status.toLowerCase().includes(needle)
      );
    });
  }, [findings, search, severity]);

  return (
    <DashboardShell title="Findings" subtitle="Vulnerabilities discovered in this project.">
      <ProjectNav projectName={project?.name} active="findings" />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-6"
      >
        <h2 className="mb-4 text-lg font-semibold text-brand-100">All findings</h2>
        <div className="mb-4 grid gap-3 sm:grid-cols-[1fr_12rem]">
          <ListSearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search findings..."
          />
          <select
            value={severity}
            onChange={(event) => setSeverity(event.target.value)}
            className="input-field"
            aria-label="Filter by severity"
          >
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        {loading ? (
          <ListSkeleton rows={4} />
        ) : filteredFindings.length === 0 ? (
          <EmptyState
            compact
            icon={Bug}
            title={search || severity ? "No matching findings" : "No findings yet"}
            description={
              search || severity
                ? "Adjust your search or severity filter."
                : "Run a scan to populate results."
            }
          />
        ) : (
          <ul className="space-y-3">
            {filteredFindings.map((finding) => (
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
