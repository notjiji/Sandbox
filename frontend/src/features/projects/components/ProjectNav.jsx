import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Bug, FileText, Globe, LayoutGrid, Radar } from "lucide-react";

export default function ProjectNav({ projectName, assetName, active }) {
  const { projectId, assetId } = useParams();

  const projectTabs = [
    { key: "assets", label: "Assets", icon: Globe, path: `/projects/${projectId}/assets` },
    { key: "findings", label: "Findings", icon: Bug, path: `/projects/${projectId}/findings` },
    { key: "reports", label: "Reports", icon: FileText, path: `/projects/${projectId}/reports` },
    { key: "risk", label: "Risk", icon: Radar, path: `/projects/${projectId}` },
  ];

  const assetTabs = [
    { key: "overview", label: "Overview", icon: LayoutGrid, path: `/projects/${projectId}/assets/${assetId}` },
    { key: "scans", label: "Scans", icon: Radar, path: `/projects/${projectId}/assets/${assetId}/scans` },
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
