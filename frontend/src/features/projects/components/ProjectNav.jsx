import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Bug, FileText, Radar } from "lucide-react";

const tabs = [
  { to: "scans", label: "Scans", icon: Radar },
  { to: "findings", label: "Findings", icon: Bug },
  { to: "reports", label: "Reports", icon: FileText },
];

export default function ProjectNav({ projectName, active }) {
  const { projectId } = useParams();

  return (
    <div className="mb-6 space-y-4">
      <Link to="/projects" className="link-glow inline-flex items-center gap-2 text-sm">
        <ArrowLeft size={16} />
        All projects
      </Link>

      {projectName && (
        <p className="terminal-text text-brand-500">
          {">"} project/{projectName}
        </p>
      )}

      <nav className="flex flex-wrap gap-2">
        {tabs.map(({ to, label, icon: Icon }) => {
          const path = `/projects/${projectId}/${to}`;
          const isActive = active === to;

          return (
            <Link
              key={to}
              to={path}
              className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm transition ${
                isActive
                  ? "border-brand-500/50 bg-brand-900/40 text-brand-100"
                  : "border-brand-800/50 text-brand-400 hover:border-brand-600/40 hover:text-brand-200"
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
