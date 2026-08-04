const ACTIVE_ORG_ID_KEY = "sandbox_active_org_id";
const RECENT_ORG_IDS_KEY = "sandbox_recent_org_ids";
const MAX_RECENT_ORGS = 5;

function readRecentOrgIds(): string[] {
  try {
    const raw = localStorage.getItem(RECENT_ORG_IDS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === "string") : [];
  } catch {
    return [];
  }
}

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

  /** Most-recently-used org ids (newest first), excluding invalid entries. */
  getRecentOrgIds(): string[] {
    return readRecentOrgIds();
  },

  /** Record an org visit and bump it to the front of the recent list. */
  recordRecentOrg(organizationId: string): void {
    if (!organizationId) return;
    const recent = readRecentOrgIds().filter((id) => id !== organizationId);
    recent.unshift(organizationId);
    localStorage.setItem(RECENT_ORG_IDS_KEY, JSON.stringify(recent.slice(0, MAX_RECENT_ORGS)));
  },
};
