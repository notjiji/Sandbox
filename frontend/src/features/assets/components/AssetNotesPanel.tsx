import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Save, StickyNote } from "lucide-react";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { AssetSummary } from "@/shared/types/asset";
import { assetsApi } from "../api";

interface AssetNotesPanelProps {
  projectId: string;
  asset: AssetSummary;
  onSaved?: () => void;
}

export default function AssetNotesPanel({
  projectId,
  asset,
  onSaved,
}: AssetNotesPanelProps) {
  const [editing, setEditing] = useState(false);
  const [notes, setNotes] = useState(asset.notes ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const readOnly = asset.status === "deleted";

  useEffect(() => {
    setNotes(asset.notes ?? "");
    setEditing(false);
    setError(null);
  }, [asset.id, asset.notes]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await assetsApi.update(projectId, asset.id, {
        notes: notes.trim() || undefined,
      });
      setEditing(false);
      onSaved?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to save notes.");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setNotes(asset.notes ?? "");
    setEditing(false);
    setError(null);
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel p-6"
    >
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-brand-800/50 bg-brand-950/40 p-2">
            <StickyNote size={18} className="text-brand-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-brand-100">Notes</h2>
            <p className="text-sm text-brand-500">
              Internal context for your team — not included in reports.
            </p>
          </div>
        </div>
        {!readOnly && !editing && (
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="btn-ghost text-sm"
          >
            {asset.notes ? "Edit notes" : "Add notes"}
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4">
          <FormAlert message={error} />
        </div>
      )}

      {editing ? (
        <div className="space-y-3">
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={6}
            maxLength={10000}
            placeholder="Add runbooks, ownership context, remediation notes..."
            className="w-full rounded-lg border border-brand-800/60 bg-brand-950/40 px-4 py-3 text-sm text-brand-100 placeholder:text-brand-600 focus:border-brand-600 focus:outline-none"
          />
          <div className="flex justify-end gap-2">
            <button type="button" onClick={handleCancel} className="btn-ghost text-sm">
              Cancel
            </button>
            <button
              type="button"
              onClick={() => void handleSave()}
              disabled={saving}
              className="btn-primary inline-flex items-center gap-2 text-sm"
            >
              <Save size={16} />
              {saving ? "Saving..." : "Save notes"}
            </button>
          </div>
        </div>
      ) : asset.notes ? (
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-brand-200">{asset.notes}</p>
      ) : (
        <p className="text-sm text-brand-500">
          {readOnly
            ? "No notes recorded for this asset."
            : "No notes yet. Add context your team should remember about this asset."}
        </p>
      )}
    </motion.section>
  );
}
