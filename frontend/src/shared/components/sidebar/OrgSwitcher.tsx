import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Building2, Check, ChevronDown, Plus } from "lucide-react";
import { organizationsApi } from "@/features/organizations/api";
import { switchOrganization, syncOrganizations } from "@/features/organizations/org";
import { orgStorage } from "@/features/organizations/storage";
import type { OrganizationSummary } from "@/shared/types/organization";
import { cn } from "@/shared/lib/utils";

interface OrgSwitcherProps {
  collapsed?: boolean;
  onNavigate?: () => void;
}

function OrgInitial({ name }: { name: string }) {
  return (
    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-brand-600/50 bg-brand-900/60 text-sm font-semibold text-brand-200">
      {name.charAt(0).toUpperCase()}
    </span>
  );
}

export default function OrgSwitcher({ collapsed = false, onNavigate }: OrgSwitcherProps) {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const [organizations, setOrganizations] = useState<OrganizationSummary[]>([]);
  const [activeOrgId, setActiveOrgId] = useState<string | null>(orgStorage.getActiveOrgId());
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);

  const activeOrg = organizations.find((org) => org.id === activeOrgId) ?? organizations[0];

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

  useEffect(() => {
    if (!open) return undefined;

    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  const handleSelect = async (organizationId: string) => {
    if (organizationId === activeOrgId || switching) return;

    setSwitching(true);
    try {
      await switchOrganization(organizationsApi, organizationId);
      setActiveOrgId(organizationId);
      setOpen(false);
      onNavigate?.();
      navigate("/dashboard", { replace: true });
    } catch {
      navigate("/select-organization");
    } finally {
      setSwitching(false);
    }
  };

  if (loading || organizations.length === 0 || !activeOrg) {
    return null;
  }

  const dropdown = open && (
    <div
      className={cn(
        "absolute z-50 min-w-[14rem] rounded-xl border border-brand-700/60 bg-void-100/95 py-2 shadow-crt backdrop-blur-md",
        collapsed ? "left-full top-0 ml-2 w-56" : "left-0 right-0 top-full mt-2",
      )}
      role="listbox"
      aria-label="Organizations"
    >
      <div className="px-3 py-2">
        <p className="text-[10px] font-medium uppercase tracking-wider text-brand-600">
          Organizations
        </p>
      </div>

      <ul className="max-h-56 overflow-y-auto px-1">
        {organizations.map((org) => {
          const isActive = org.id === activeOrgId;
          return (
            <li key={org.id}>
              <button
                type="button"
                role="option"
                aria-selected={isActive}
                disabled={switching}
                onClick={() => void handleSelect(org.id)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition",
                  isActive
                    ? "bg-brand-900/50 text-brand-100"
                    : "text-brand-300 hover:bg-brand-900/30 hover:text-brand-100",
                )}
              >
                <OrgInitial name={org.name} />
                <span className="min-w-0 flex-1 truncate font-medium">{org.name}</span>
                {isActive && <Check size={16} className="shrink-0 text-brand-400" />}
              </button>
            </li>
          );
        })}
      </ul>

      <div className="my-2 border-t border-brand-800/50" />

      <Link
        to="/select-organization"
        onClick={() => {
          setOpen(false);
          onNavigate?.();
        }}
        className="mx-1 flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm text-brand-300 transition hover:bg-brand-900/30 hover:text-brand-100"
      >
        <Plus size={16} className="text-brand-400" />
        Create organization
      </Link>
    </div>
  );

  if (collapsed) {
    return (
      <div ref={containerRef} className="relative flex justify-center">
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-brand-700/50 bg-brand-950/50 text-brand-300 transition hover:border-brand-500/40 hover:bg-brand-900/40"
          title={activeOrg.name}
          aria-label={`Switch organization. Current: ${activeOrg.name}`}
          aria-expanded={open}
          aria-haspopup="listbox"
        >
          <Building2 size={16} />
        </button>
        {dropdown}
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        disabled={switching}
        className={cn(
          "flex w-full items-center gap-3 rounded-lg border border-brand-700/50 bg-brand-950/50 px-3 py-2.5 text-left transition",
          "hover:border-brand-500/40 hover:bg-brand-900/40",
          open && "border-brand-500/50 bg-brand-900/40",
        )}
        aria-label="Switch organization"
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <OrgInitial name={activeOrg.name} />
        <span className="min-w-0 flex-1 truncate text-sm font-medium text-brand-100">
          {activeOrg.name}
        </span>
        <ChevronDown
          size={16}
          className={cn(
            "shrink-0 text-brand-500 transition-transform",
            open && "rotate-180",
          )}
          aria-hidden
        />
      </button>
      {dropdown}
      <p className="mt-1.5 px-1 text-[10px] text-brand-600">
        {organizations.length > 1 ? "Switch workspace" : "Your workspace"}
      </p>
    </div>
  );
}
