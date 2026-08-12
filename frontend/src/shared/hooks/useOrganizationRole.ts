import { useEffect, useState } from "react";
import { organizationsApi } from "@/features/organizations/api";
import { orgStorage } from "@/features/organizations/storage";
import type { OrganizationRole } from "@/shared/types/organization";

const SCAN_RUN_ROLES: OrganizationRole[] = ["owner", "admin", "security_analyst"];
const REPORT_GENERATE_ROLES: OrganizationRole[] = ["owner", "admin", "security_analyst", "manager"];
const REPORT_DELETE_ROLES: OrganizationRole[] = ["owner", "admin", "security_analyst"];
const MANAGE_ROLES: OrganizationRole[] = ["owner", "admin"];
const MONITORING_MANAGE_ROLES: OrganizationRole[] = ["owner", "admin", "security_analyst"];

export function useOrganizationRole() {
  const [role, setRole] = useState<OrganizationRole | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const orgs = await organizationsApi.listMine();
        if (!active) return;
        const activeOrgId = orgStorage.getActiveOrgId();
        const current = orgs?.items.find((org) => org.id === activeOrgId);
        setRole((current?.role as OrganizationRole) ?? null);
      } catch {
        if (active) setRole(null);
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  return {
    role,
    loading,
    canRunScan: role != null && SCAN_RUN_ROLES.includes(role),
    canGenerateReport: role != null && REPORT_GENERATE_ROLES.includes(role),
    canDeleteReport: role != null && REPORT_DELETE_ROLES.includes(role),
    canManage: role != null && MANAGE_ROLES.includes(role),
    canManageMonitoring: role != null && MONITORING_MANAGE_ROLES.includes(role),
  };
}
