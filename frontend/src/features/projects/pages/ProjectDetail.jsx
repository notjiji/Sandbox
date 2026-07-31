import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Bug, FileText, Radar } from "lucide-react";
import DashboardShell from "@/features/organizations/components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import { projectsApi } from "../api";
import ProjectNav from "../components/ProjectNav";

const sections = [
  {
    key: "scans",
    title: "Scans",
    description: "Launch and monitor security scans against project assets.",
    icon: Radar,
  },
  {
    key: "findings",
    title: "Findings",
    description: "Review vulnerabilities discovered across completed scans.",
    icon: Bug,
  },
  {
    key: "reports",
    title: "Reports",
    description: "Generate and download executive or technical reports.",
    icon: FileText,
  },
];

export default function ProjectDetail() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [alert, setAlert] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const response = await projectsApi.get(projectId);
        if (active) setProject(response?.data ?? null);
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Unable to load project.");
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

  return (
    <DashboardShell
      title={project?.name ?? "Project"}
      subtitle={project?.description ?? "Project workspace"}
    >
      {alert && <FormAlert message={alert} />}
      <ProjectNav projectName={project?.name} />

      {loading ? (
        <p className="text-brand-500">Loading project...</p>
      ) : !project ? (
        <p className="text-brand-500">Project not found.</p>
      ) : (
        <div className="grid gap-6 md:grid-cols-3">
          {sections.map(({ key, title, description, icon: Icon }, index) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Link
                to={`/projects/${projectId}/${key}`}
                className="glass-panel block h-full p-6 transition hover:border-brand-500/40"
              >
                <Icon size={24} className="mb-4 text-brand-400" />
                <h2 className="text-xl font-semibold text-brand-100">{title}</h2>
                <p className="mt-2 text-sm text-brand-500">{description}</p>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </DashboardShell>
  );
}
