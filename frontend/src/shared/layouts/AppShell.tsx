import type { ReactNode } from "react";
import SidebarLayout from "@/shared/layouts/SidebarLayout";

interface AppShellProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  showOrgContext?: boolean;
}

export default function AppShell({
  children,
  title,
  subtitle,
  showOrgContext = false,
}: AppShellProps) {
  return (
    <SidebarLayout title={title} subtitle={subtitle} showOrgContext={showOrgContext} maxWidth="md">
      {children}
    </SidebarLayout>
  );
}
