import { useLocation, useParams } from "react-router-dom";
import { PanelLeftClose, PanelLeftOpen, X } from "lucide-react";
import Logo from "@/shared/components/Logo";
import { MAIN_NAV_ITEMS } from "@/shared/config/navigation";
import { cn } from "@/shared/lib/utils";
import OrgSwitcher from "./OrgSwitcher";
import PinnedProjects from "./PinnedProjects";
import QuickActions from "./QuickActions";
import SidebarNavLink from "./SidebarNavLink";
import SidebarUserSection from "./SidebarUserSection";

interface SidebarProps {
  collapsed: boolean;
  mobile?: boolean;
  onToggleCollapse?: () => void;
  onCloseMobile?: () => void;
  showOrgSwitcher?: boolean;
}

export default function Sidebar({
  collapsed,
  mobile = false,
  onToggleCollapse,
  onCloseMobile,
  showOrgSwitcher = true,
}: SidebarProps) {
  const { pathname } = useLocation();
  const { projectId } = useParams<{ projectId?: string }>();
  const navContext = { pathname, projectId };

  const handleNavigate = () => {
    onCloseMobile?.();
  };

  return (
    <aside
      id="app-sidebar"
      className={cn(
        "flex h-full flex-col border-r border-brand-800/40 bg-void/95 backdrop-blur-md",
        collapsed && !mobile ? "w-[4.5rem]" : "w-64",
        mobile && "w-64 shadow-glow-lg",
      )}
      aria-label="Application sidebar"
    >
      <div
        className={cn(
          "flex items-center border-b border-brand-800/40 px-3 py-4",
          collapsed && !mobile ? "justify-center" : "justify-between gap-2",
        )}
      >
        <Logo size="sm" to="/dashboard" showText={!collapsed || mobile} />
        {mobile ? (
          <button
            type="button"
            onClick={onCloseMobile}
            className="btn-ghost p-2"
            aria-label="Close navigation menu"
          >
            <X size={18} />
          </button>
        ) : (
          onToggleCollapse && (
            <button
              type="button"
              onClick={onToggleCollapse}
              className="btn-ghost hidden p-2 lg:inline-flex"
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              aria-expanded={!collapsed}
              aria-controls="app-sidebar"
            >
              {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
            </button>
          )
        )}
      </div>

      {showOrgSwitcher && (
        <div className={cn("border-b border-brand-800/40 px-3 py-3", collapsed && "px-2")}>
          <OrgSwitcher collapsed={collapsed && !mobile} onNavigate={onCloseMobile} />
        </div>
      )}

      {showOrgSwitcher && (
        <div className={cn("border-b border-brand-800/40 px-3 py-3", collapsed && "px-2")}>
          <QuickActions collapsed={collapsed && !mobile} onNavigate={handleNavigate} />
        </div>
      )}

      {showOrgSwitcher && (
        <PinnedProjects collapsed={collapsed && !mobile} onNavigate={handleNavigate} />
      )}

      <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-3" aria-label="Main">
        {MAIN_NAV_ITEMS.map((item) => (
          <SidebarNavLink
            key={item.id}
            to={item.resolveHref(navContext)}
            label={item.label}
            icon={item.icon}
            active={item.isActive(pathname)}
            collapsed={collapsed && !mobile}
            disabled={item.disabled}
            badge={item.badge}
            onNavigate={handleNavigate}
          />
        ))}
      </nav>

      <div className={cn("px-2 pb-4", collapsed && "px-1")}>
        <SidebarUserSection
          collapsed={collapsed && !mobile}
          profileActive={pathname === "/profile"}
          onNavigate={handleNavigate}
        />
      </div>
    </aside>
  );
}
