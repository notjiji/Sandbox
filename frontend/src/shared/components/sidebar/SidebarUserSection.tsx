import { Link, useNavigate } from "react-router-dom";
import { LogOut, User } from "lucide-react";
import { authApi } from "@/features/auth/api";
import { tokenStorage } from "@/features/auth/storage";
import { orgStorage } from "@/features/organizations/storage";
import SidebarNavLink from "./SidebarNavLink";
import { cn } from "@/shared/lib/utils";

interface SidebarUserSectionProps {
  collapsed?: boolean;
  profileActive?: boolean;
  onNavigate?: () => void;
}

export default function SidebarUserSection({
  collapsed = false,
  profileActive = false,
  onNavigate,
}: SidebarUserSectionProps) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      tokenStorage.clear();
      orgStorage.clear();
    }
    navigate("/login");
  };

  return (
    <div className={cn("space-y-1 border-t border-brand-800/50 pt-3", collapsed && "pt-2")}>
      {!collapsed && (
        <p className="px-3 pb-1 text-[10px] uppercase tracking-wider text-brand-600">Account</p>
      )}
      <SidebarNavLink
        to="/profile"
        label="User Profile"
        icon={User}
        active={profileActive}
        collapsed={collapsed}
        onNavigate={onNavigate}
      />
      <button
        type="button"
        onClick={() => {
          void handleLogout();
          onNavigate?.();
        }}
        className={cn(
          "flex w-full items-center gap-3 rounded-lg border border-transparent px-3 py-2.5 text-sm text-brand-400 transition-colors",
          "hover:border-brand-700/50 hover:bg-brand-950/60 hover:text-brand-200",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-void",
          collapsed && "justify-center px-2",
        )}
        title={collapsed ? "Sign out" : undefined}
      >
        <LogOut size={18} aria-hidden />
        {!collapsed && <span className="font-dyslexic">Sign out</span>}
      </button>
      {!collapsed && (
        <p className="px-3 pt-1">
          <Link to="/select-organization" className="text-xs text-brand-600 hover:text-brand-400">
            Manage organizations
          </Link>
        </p>
      )}
    </div>
  );
}
