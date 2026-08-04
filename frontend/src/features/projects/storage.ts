const PINNED_PROJECTS_KEY = "sandbox_pinned_projects";

type PinnedProjectsMap = Record<string, string[]>;

function readMap(): PinnedProjectsMap {
  try {
    const raw = localStorage.getItem(PINNED_PROJECTS_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return {};
    return parsed as PinnedProjectsMap;
  } catch {
    return {};
  }
}

function writeMap(map: PinnedProjectsMap): void {
  localStorage.setItem(PINNED_PROJECTS_KEY, JSON.stringify(map));
}

export const projectStorage = {
  getPinnedProjectIds(organizationId: string): string[] {
    if (!organizationId) return [];
    return readMap()[organizationId] ?? [];
  },

  isPinned(organizationId: string, projectId: string): boolean {
    return this.getPinnedProjectIds(organizationId).includes(projectId);
  },

  togglePinned(organizationId: string, projectId: string): boolean {
    if (!organizationId || !projectId) return false;
    const map = readMap();
    const current = map[organizationId] ?? [];
    const isPinned = current.includes(projectId);
    map[organizationId] = isPinned
      ? current.filter((id) => id !== projectId)
      : [projectId, ...current];
    writeMap(map);
    return !isPinned;
  },

  setPinned(organizationId: string, projectId: string, pinned: boolean): void {
    if (!organizationId || !projectId) return;
    const map = readMap();
    const current = map[organizationId] ?? [];
    if (pinned && !current.includes(projectId)) {
      map[organizationId] = [projectId, ...current];
    } else if (!pinned) {
      map[organizationId] = current.filter((id) => id !== projectId);
    }
    writeMap(map);
  },
};
