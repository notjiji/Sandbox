import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import { organizationsApi } from "@/features/organizations/api";
import { setValidatedActiveOrg, syncOrganizations } from "@/features/organizations/org";
import { orgStorage } from "@/features/organizations/storage";
import type { OrganizationSummary } from "@/shared/types/organization";
import { cn } from "@/shared/lib/utils";

interface OrgSwitcherProps {
  collapsed?: boolean;
}

export default function OrgSwitcher({ collapsed = false }: OrgSwitcherProps) {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<OrganizationSummary[]>([]);
  const [activeOrgId, setActiveOrgId] = useState<string | null>(orgStorage.getActiveOrgId());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const synced = await syncOrganizations(organizationsApi);
        if (!active) return;
        setOrganizations(synced.activeOrganizations);
        setActiveOrgId(synced.activeOrgId);
      } catch {
        if (active) setOrganizations([]);
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  const handleChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const nextOrgId = event.target.value;
    if (!nextOrgId || nextOrgId === activeOrgId) return;

    try {
      const payload = await organizationsApi.listMine();
      setValidatedActiveOrg(nextOrgId, payload);
      setActiveOrgId(nextOrgId);
      window.location.reload();
    } catch {
      navigate("/select-organization");
    }
  };

  if (loading || organizations.length === 0) {
    return null;
  }

  if (collapsed) {
    return (
      <div
        className="mx-auto flex h-9 w-9 items-center justify-center rounded-lg border border-brand-700/50 bg-brand-950/50 text-xs font-bold text-brand-300"
        title={organizations.find((o) => o.id === activeOrgId)?.name ?? "Organization"}
        aria-label="Active organization"
      >
        {(organizations.find((o) => o.id === activeOrgId)?.name ?? "?").charAt(0).toUpperCase()}
      </div>
    );
  }

  return (
    <div className="relative">
      <label htmlFor="org-switcher" className="sr-only">
        Active organization
      </label>
      <select
        id="org-switcher"
        value={activeOrgId ?? ""}
        onChange={handleChange}
        className={cn(
          "input-field w-full appearance-none py-2 pl-3 pr-9 text-sm",
          organizations.length < 2 && "cursor-default opacity-90",
        )}
        disabled={organizations.length < 2}
        aria-describedby="org-switcher-hint"
      >
        {organizations.map((org) => (
          <option key={org.id} value={org.id}>
            {org.name}
          </option>
        ))}
      </select>
      {organizations.length >= 2 && (
        <ChevronDown
          size={16}
          className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-brand-500"
          aria-hidden
        />
      )}
      <p id="org-switcher-hint" className="mt-1 px-1 text-[10px] text-brand-600">
        {organizations.length >= 2 ? "Switch workspace" : "Single workspace"}
      </p>
    </div>
  );
}
