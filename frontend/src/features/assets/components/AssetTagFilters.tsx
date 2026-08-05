import { BookmarkPlus, ChevronDown, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";
import type { AssetSavedFilterSummary, AssetTagFacet } from "@/shared/types/asset";
import { assetsApi } from "../api";
import type { AssetFiltersState } from "../utils/hierarchy";

interface AssetTagFiltersProps {
  projectId: string;
  selectedTags: string[];
  onChange: (tags: string[]) => void;
}

function formatTagLabel(tag: string): string {
  return tag
    .split(/[_-]/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default function AssetTagFilters({
  projectId,
  selectedTags,
  onChange,
}: AssetTagFiltersProps) {
  const [facets, setFacets] = useState<AssetTagFacet[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    assetsApi
      .tags(projectId)
      .then((response) => {
        if (active) setFacets(response?.items ?? []);
      })
      .catch(() => {
        if (active) setFacets([]);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [projectId]);

  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      onChange(selectedTags.filter((item) => item !== tag));
      return;
    }
    onChange([...selectedTags, tag]);
  };

  return (
    <div className="space-y-3">
      {selectedTags.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-brand-500">
            Active
          </span>
          {selectedTags.map((tag, index) => (
            <span key={tag} className="inline-flex items-center gap-1">
              <button
                type="button"
                onClick={() => toggleTag(tag)}
                className="rounded-full border border-brand-400/60 bg-brand-800/50 px-3 py-1 text-xs text-brand-100 hover:border-brand-300"
              >
                {formatTagLabel(tag)} ×
              </button>
              {index < selectedTags.length - 1 && (
                <span className="text-xs text-brand-600">+</span>
              )}
            </span>
          ))}
          <button
            type="button"
            onClick={() => onChange([])}
            className="text-xs text-brand-500 hover:text-brand-300"
          >
            Clear tags
          </button>
        </div>
      )}

      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-500">
          Tags
        </p>
        {loading ? (
          <p className="text-sm text-brand-600">Loading tags...</p>
        ) : facets.length === 0 ? (
          <p className="text-sm text-brand-600">No tags yet. Add tags when creating or editing assets.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {facets.map((facet) => {
              const active = selectedTags.includes(facet.tag);
              return (
                <button
                  key={facet.tag}
                  type="button"
                  onClick={() => toggleTag(facet.tag)}
                  className={`rounded-full border px-3 py-1 text-xs transition ${
                    active
                      ? "border-brand-400 bg-brand-800/60 text-brand-100"
                      : "border-brand-800/60 bg-brand-950/20 text-brand-400 hover:border-brand-600 hover:text-brand-200"
                  }`}
                >
                  {formatTagLabel(facet.tag)}
                  <span className="ml-1 text-brand-600">{facet.count}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

interface AssetSavedFiltersProps {
  projectId: string;
  filters: AssetFiltersState;
  onApply: (filters: AssetFiltersState) => void;
}

export function AssetSavedFiltersMenu({ projectId, filters, onApply }: AssetSavedFiltersProps) {
  const [saved, setSaved] = useState<AssetSavedFilterSummary[]>([]);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const loadSaved = () => {
    assetsApi
      .savedFilters(projectId)
      .then((response) => setSaved(response?.items ?? []))
      .catch(() => setSaved([]));
  };

  useEffect(() => {
    loadSaved();
  }, [projectId]);

  const handleSave = async () => {
    const name = window.prompt("Name this filter preset");
    if (!name?.trim()) return;
    setSaving(true);
    try {
      await assetsApi.createSavedFilter(projectId, {
        name: name.trim(),
        filters: {
          search: filters.search,
          tags: filters.tags,
          type: filters.type,
          status: filters.status,
          environment: filters.environment,
          criticality: filters.criticality,
          asset_category: filters.asset_category,
          sort: filters.sort,
          order: filters.order,
        },
      });
      toast.success("Filter saved.");
      loadSaved();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to save filter.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (filterId: string) => {
    try {
      await assetsApi.deleteSavedFilter(projectId, filterId);
      setSaved((current) => current.filter((item) => item.id !== filterId));
      toast.success("Saved filter removed.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Unable to delete filter.");
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="btn-ghost inline-flex items-center gap-2"
      >
        Saved filters
        <ChevronDown size={14} className={open ? "rotate-180" : ""} />
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-72 rounded-lg border border-brand-800/60 bg-void-100 p-3 shadow-xl">
          <button
            type="button"
            disabled={saving}
            onClick={() => void handleSave()}
            className="mb-3 inline-flex w-full items-center justify-center gap-2 rounded-md border border-brand-700/50 px-3 py-2 text-sm text-brand-200 hover:border-brand-500/40"
          >
            <BookmarkPlus size={14} />
            Save current filter
          </button>

          {saved.length === 0 ? (
            <p className="text-sm text-brand-600">No saved filters yet.</p>
          ) : (
            <ul className="space-y-2">
              {saved.map((item) => (
                <li
                  key={item.id}
                  className="flex items-center justify-between gap-2 rounded-md border border-brand-800/40 px-3 py-2"
                >
                  <button
                    type="button"
                    onClick={() => {
                      onApply(item.filters);
                      setOpen(false);
                    }}
                    className="min-w-0 flex-1 text-left text-sm text-brand-200 hover:text-brand-50"
                  >
                    {item.name}
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleDelete(item.id)}
                    className="text-brand-600 hover:text-red-300"
                    aria-label={`Delete ${item.name}`}
                  >
                    <Trash2 size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
