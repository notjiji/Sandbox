import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Activity,
  Bug,
  FileText,
  Globe,
  LayoutDashboard,
  Radar,
  Settings,
} from "lucide-react";

interface ProjectNavProps {
  projectName?: string;
  assetName?: string;
  active: string;
}

export default function ProjectNav({ projectName, assetName, active }: ProjectNavProps) {
  const { projectId, assetId } = useParams<{ projectId: string; assetId?: string }>();

  const projectTabs = [
    {
      key: "overview",
      label: "Overview",
      icon: LayoutDashboard,
      path: `/projects/${projectId}`,
    },
    { key: "assets", label: "Assets", icon: Globe, path: `/projects/${projectId}/assets` },
    { key: "findings", label: "Findings", icon: Bug, path: `/projects/${projectId}/findings` },
    { key: "reports", label: "Reports", icon: FileText, path: `/projects/${projectId}/reports` },
    {
      key: "settings",
      label: "Settings",
      icon: Settings,
      path: `/projects/${projectId}/settings`,
    },
  ];

  const assetTabs = [
    {
      key: "overview",
      label: "Overview",
      icon: LayoutDashboard,
      path: `/projects/${projectId}/assets/${assetId}`,
    },
    {
      key: "findings",
      label: "Findings",
      icon: Bug,
      path: `/projects/${projectId}/assets/${assetId}/findings`,
    },
    {
      key: "reports",
      label: "Reports",
      icon: FileText,
      path: `/projects/${projectId}/assets/${assetId}/reports`,
    },
    {
      key: "scans",
      label: "Scans",
      icon: Radar,
      path: `/projects/${projectId}/assets/${assetId}/scans`,
    },
    {
      key: "monitoring",
      label: "Monitoring",
      icon: Activity,
      path: `/projects/${projectId}/assets/${assetId}/monitoring`,
    },
    { key: "assets", label: "All assets", icon: Globe, path: `/projects/${projectId}/assets` },
  ];

  const tabs = assetId ? assetTabs : projectTabs;

  return (
    <div className="mb-6 space-y-4">
      <Link to="/projects" className="link-glow inline-flex items-center gap-2 text-sm">
        <ArrowLeft size={16} />
        All projects
      </Link>

      {projectName && (
        <p className="terminal-text text-brand-500">
          {">"} project/{projectName}
          {assetName ? ` / asset/${assetName}` : ""}
        </p>
      )}

      <nav className="flex flex-wrap gap-2">
        {tabs.map(({ key, label, icon: Icon, path }) => (
          <Link
            key={key}
            to={path}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition ${
              active === key
                ? "border-brand-500/50 bg-brand-900/40 text-brand-100"
                : "border-brand-800/50 text-brand-400 hover:border-brand-600/40 hover:text-brand-200"
            }`}
          >
            <Icon size={16} />
            {label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
