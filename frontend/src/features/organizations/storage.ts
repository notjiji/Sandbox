const ACTIVE_ORG_ID_KEY = "sandbox_active_org_id";

export const orgStorage = {
  setActiveOrgId(organizationId: string): void {
    if (organizationId) {
      localStorage.setItem(ACTIVE_ORG_ID_KEY, organizationId);
    }
  },

  getActiveOrgId(): string | null {
    return localStorage.getItem(ACTIVE_ORG_ID_KEY);
  },

  clear(): void {
    localStorage.removeItem(ACTIVE_ORG_ID_KEY);
  },
};
