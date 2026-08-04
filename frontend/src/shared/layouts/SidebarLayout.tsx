import { motion } from "framer-motion";
import { Menu } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { unwrapData } from "@/shared/api/client";
import { organizationsApi } from "@/features/organizations/api";
import Sidebar from "@/shared/components/sidebar/Sidebar";
import { useSidebarState } from "@/shared/hooks/useSidebarState";
import type { OrganizationDetail } from "@/shared/types/organization";
import { cn } from "@/shared/lib/utils";

interface SidebarLayoutProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  /** Show org switcher and org slug in header (org-scoped pages). */
  showOrgContext?: boolean;
  maxWidth?: "md" | "lg" | "xl" | "full";
}

const maxWidthClass: Record<NonNullable<SidebarLayoutProps["maxWidth"]>, string> = {
  md: "max-w-3xl",
  lg: "max-w-6xl",
  xl: "max-w-7xl",
  full: "max-w-none",
};

export default function SidebarLayout({
  children,
  title,
  subtitle,
  showOrgContext = true,
  maxWidth = "lg",
}: SidebarLayoutProps) {
  const { collapsed, toggleCollapsed, mobileOpen, toggleMobile, closeMobile } = useSidebarState();
  const [currentOrg, setCurrentOrg] = useState<OrganizationDetail | null>(null);

  useEffect(() => {
    if (!showOrgContext) return;

    let active = true;

    async function loadOrg() {
      try {
        const detail = unwrapData(await organizationsApi.getCurrent());
        if (active) setCurrentOrg(detail);
      } catch {
        if (active) setCurrentOrg(null);
      }
    }

    void loadOrg();
    return () => {
      active = false;
    };
  }, [showOrgContext]);

  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <div className="crt-vignette scanlines noise-bg relative flex min-h-screen overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(rgba(162,98,162,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(162,98,162,0.08) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-brand-900 focus:px-4 focus:py-2 focus:text-brand-50"
      >
        Skip to main content
      </a>

      {/* Desktop sidebar */}
      <div className="relative z-20 hidden shrink-0 lg:block">
        <Sidebar
          collapsed={collapsed}
          onToggleCollapse={toggleCollapsed}
          showOrgSwitcher={showOrgContext}
        />
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-40 bg-black/60 lg:hidden"
            aria-label="Close navigation menu"
            onClick={closeMobile}
          />
          <div className="fixed inset-y-0 left-0 z-50 lg:hidden">
            <Sidebar mobile collapsed={false} onCloseMobile={closeMobile} showOrgSwitcher={showOrgContext} />
          </div>
        </>
      )}

      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-brand-800/40 bg-void/60 px-4 py-3 backdrop-blur-sm lg:hidden">
          <button
            type="button"
            onClick={toggleMobile}
            className="btn-ghost p-2"
            aria-label="Open navigation menu"
            aria-expanded={mobileOpen}
            aria-controls="app-sidebar"
          >
            <Menu size={20} />
          </button>
          <span className="font-dyslexic text-sm text-brand-300">Sandbox</span>
        </header>

        <main id="main-content" className={cn("mx-auto w-full flex-1 px-4 py-8 sm:px-6", maxWidthClass[maxWidth])}>
          {(title || subtitle || (showOrgContext && currentOrg)) && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8"
            >
              {showOrgContext && currentOrg && (
                <p className="terminal-text text-brand-500">{">"} {currentOrg.slug}</p>
              )}
              {title && <h1 className="mt-2 text-3xl font-bold text-brand-50">{title}</h1>}
              {subtitle && <p className="mt-2 text-brand-400">{subtitle}</p>}
            </motion.div>
          )}
          {children}
        </main>

        <footer className="border-t border-brand-900/40 py-4 text-center">
          <p className="terminal-text text-brand-600">sys.sandbox v1.0.0 // authenticated session</p>
        </footer>
      </div>
    </div>
  );
}
