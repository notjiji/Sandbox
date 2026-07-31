import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Building2,
  FolderKanban,
  LayoutDashboard,
  LogOut,
  Settings,
  User,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
import Logo from "./Logo";
import { authApi, orgApi, unwrapData } from "../lib/api";
import { tokenStorage } from "../lib/auth";
import {
  getActiveOrganizations,
  orgStorage,
  setValidatedActiveOrg,
  syncOrganizations,
} from "../lib/org";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/organization/settings", label: "Organization", icon: Building2 },
  { to: "/organization/members", label: "Members", icon: Users },
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/profile", label: "Profile", icon: User },
];

export default function DashboardShell({ children, title, subtitle }) {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState([]);
  const [activeOrgId, setActiveOrgId] = useState(orgStorage.getActiveOrgId());
  const [currentOrg, setCurrentOrg] = useState(null);

  useEffect(() => {
    let active = true;

    async function loadOrgContext() {
      try {
        const synced = await syncOrganizations(orgApi);
        if (!active) return;
        setOrganizations(synced.activeOrganizations);
        setActiveOrgId(synced.activeOrgId);
        if (synced.activeOrgId) {
          const detail = unwrapData(await orgApi.getCurrent());
          if (active) setCurrentOrg(detail);
        }
      } catch {
        if (active) setCurrentOrg(null);
      }
    }

    loadOrgContext();
    return () => {
      active = false;
    };
  }, [activeOrgId]);

  const handleOrgSwitch = async (event) => {
    const nextOrgId = event.target.value;
    if (!nextOrgId || nextOrgId === activeOrgId) return;

    try {
      const payload = await orgApi.listMine();
      setValidatedActiveOrg(nextOrgId, payload);
      setActiveOrgId(nextOrgId);
      window.location.reload();
    } catch {
      navigate("/select-organization");
    }
  };

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
    <div className="crt-vignette scanlines noise-bg relative min-h-screen overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(rgba(162,98,162,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(162,98,162,0.08) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <motion.header
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 border-b border-brand-800/40 bg-void/60 backdrop-blur-sm"
      >
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <Logo size="sm" />
            {organizations.length > 0 && (
              <select
                value={activeOrgId ?? ""}
                onChange={handleOrgSwitch}
                className="input-field max-w-xs text-sm"
                aria-label="Active organization"
              >
                {organizations.map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          <nav className="flex flex-wrap items-center gap-2">
            {navItems.map(({ to, label, icon: Icon }) => (
              <Link key={to} to={to} className="btn-ghost inline-flex items-center gap-2 text-sm">
                <Icon size={16} />
                {label}
              </Link>
            ))}
            <Link to="/settings" className="btn-ghost inline-flex items-center gap-2 text-sm">
              <Settings size={16} />
              Settings
            </Link>
            <button
              type="button"
              onClick={handleLogout}
              className="btn-ghost inline-flex items-center gap-2 text-sm"
            >
              <LogOut size={16} />
              Logout
            </button>
          </nav>
        </div>
      </motion.header>

      <main className="relative z-10 mx-auto max-w-6xl px-6 py-10">
        {(title || subtitle || currentOrg) && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            {currentOrg && (
              <p className="terminal-text text-brand-500">
                {">"} {currentOrg.slug}
              </p>
            )}
            {title && <h1 className="mt-2 text-3xl font-bold text-brand-50">{title}</h1>}
            {subtitle && <p className="mt-2 text-brand-400">{subtitle}</p>}
          </motion.div>
        )}
        {children}
      </main>
    </div>
  );
}
