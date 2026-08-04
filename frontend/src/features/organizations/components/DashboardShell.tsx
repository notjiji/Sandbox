import type { ReactNode } from "react";
import SidebarLayout from "@/shared/layouts/SidebarLayout";

interface DashboardShellProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
}

/** @deprecated Use SidebarLayout directly. Kept for existing page imports. */
export default function DashboardShell({ children, title, subtitle }: DashboardShellProps) {
  return (
    <SidebarLayout title={title} subtitle={subtitle} showOrgContext maxWidth="lg">
      {children}
    </SidebarLayout>
  );
}
