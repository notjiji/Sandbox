import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Bot,
  Building2,
  FileText,
  FolderKanban,
  LayoutDashboard,
  Layers,
  Radar,
  Settings,
} from "lucide-react";

export interface NavContext {
  pathname: string;
  projectId?: string;
}

export interface SidebarNavItem {
  id: string;
  label: string;
  icon: LucideIcon;
  resolveHref: (ctx: NavContext) => string;
  isActive: (pathname: string) => boolean;
  disabled?: boolean;
  badge?: string;
}

export const MAIN_NAV_ITEMS: SidebarNavItem[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
    resolveHref: () => "/dashboard",
    isActive: (path) => path === "/dashboard",
  },
  {
    id: "activity",
    label: "Activity",
    icon: Activity,
    resolveHref: () => "/organization/activity",
    isActive: (path) => path === "/organization/activity",
  },
  {
    id: "organizations",
    label: "Organizations",
    icon: Building2,
    resolveHref: () => "/organization/settings",
    isActive: (path) =>
      path.startsWith("/organization") && path !== "/organization/activity",
  },
  {
    id: "projects",
    label: "Projects",
    icon: FolderKanban,
    resolveHref: () => "/projects",
    isActive: (path) =>
      path === "/projects" ||
      (/^\/projects\/[^/]+$/.test(path) &&
        !path.includes("/assets") &&
        !path.includes("/findings") &&
        !path.includes("/reports")),
  },
  {
    id: "assets",
    label: "Assets",
    icon: Layers,
    resolveHref: ({ projectId }) =>
      projectId ? `/projects/${projectId}/assets` : "/projects",
    isActive: (path) => path.includes("/assets"),
  },
  {
    id: "scans",
    label: "Scans",
    icon: Radar,
    resolveHref: ({ projectId }) =>
      projectId ? `/projects/${projectId}/assets` : "/projects",
    isActive: (path) => path.includes("/scans"),
  },
  {
    id: "reports",
    label: "Reports",
    icon: FileText,
    resolveHref: ({ projectId }) =>
      projectId ? `/projects/${projectId}/reports` : "/projects",
    isActive: (path) => path.includes("/reports"),
  },
  {
    id: "ai-assistant",
    label: "AI Assistant",
    icon: Bot,
    resolveHref: () => "/ai-assistant",
    isActive: (path) => path.startsWith("/ai-assistant"),
    badge: "Beta",
  },
  {
    id: "settings",
    label: "Settings",
    icon: Settings,
    resolveHref: () => "/settings",
    isActive: (path) => path === "/settings",
  },
];
