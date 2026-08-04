import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { FileText, FolderPlus, Plus, Radar, UserPlus } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface QuickActionsProps {
  collapsed?: boolean;
  onNavigate?: () => void;
}

const ACTIONS = [
  {
    id: "new-project",
    label: "New Project",
    icon: FolderPlus,
    href: "/projects?create=1",
  },
  {
    id: "invite-member",
    label: "Invite Member",
    icon: UserPlus,
    href: "/organization/members",
  },
  {
    id: "run-scan",
    label: "Run Scan",
    icon: Radar,
    resolveHref: (projectId?: string) =>
      projectId ? `/projects/${projectId}/assets` : "/projects",
  },
  {
    id: "generate-report",
    label: "Generate Report",
    icon: FileText,
    resolveHref: (projectId?: string) =>
      projectId ? `/projects/${projectId}/reports` : "/projects",
  },
] as const;

export default function QuickActions({ collapsed = false, onNavigate }: QuickActionsProps) {
  const { projectId } = useParams<{ projectId?: string }>();
  const containerRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return undefined;

    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  const menu = open && (
    <div
      className={cn(
        "absolute z-50 min-w-[12rem] rounded-xl border border-brand-700/60 bg-void-100/95 py-2 shadow-crt backdrop-blur-md",
        collapsed ? "left-full top-0 ml-2 w-52" : "left-0 right-0 top-full mt-2",
      )}
      role="menu"
      aria-label="Quick actions"
    >
      <div className="px-3 py-2">
        <p className="text-[10px] font-medium uppercase tracking-wider text-brand-600">
          Quick Actions
        </p>
      </div>
      <ul className="px-1">
        {ACTIONS.map((action) => {
          const Icon = action.icon;
          const href =
            "href" in action ? action.href : action.resolveHref(projectId);
          return (
            <li key={action.id}>
              <Link
                to={href}
                role="menuitem"
                onClick={() => {
                  setOpen(false);
                  onNavigate?.();
                }}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-brand-300 transition hover:bg-brand-900/30 hover:text-brand-100"
              >
                <Icon size={16} className="shrink-0 text-brand-400" />
                {action.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );

  if (collapsed) {
    return (
      <div ref={containerRef} className="relative flex justify-center">
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-brand-600/40 bg-brand-900/40 text-brand-100 transition hover:border-brand-500/50 hover:bg-brand-800/50"
          aria-label="Quick actions"
          aria-expanded={open}
          aria-haspopup="menu"
        >
          <Plus size={18} />
        </button>
        {menu}
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={cn(
          "flex w-full items-center gap-3 rounded-lg border border-brand-600/40 bg-brand-900/40 px-3 py-2.5 text-left text-sm font-medium text-brand-100 transition",
          "hover:border-brand-500/50 hover:bg-brand-800/50",
          open && "border-brand-500/50 bg-brand-800/50",
        )}
        aria-label="Quick actions"
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-700/40">
          <Plus size={16} />
        </span>
        Quick Actions
      </button>
      {menu}
    </div>
  );
}
