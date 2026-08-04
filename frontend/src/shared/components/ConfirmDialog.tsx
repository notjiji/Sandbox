import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";

interface ConfirmDialogProps {
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  destructive = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        aria-label="Close dialog"
        onClick={onCancel}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 8 }}
        className="relative z-10 w-full max-w-md glass-panel p-6 shadow-crt"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <div className="flex items-start gap-4">
          <div
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${
              destructive
                ? "border-rose-500/30 bg-rose-950/30 text-rose-300"
                : "border-brand-600/40 bg-brand-950/40 text-brand-300"
            }`}
          >
            <AlertTriangle size={18} />
          </div>
          <div>
            <h2 id="confirm-dialog-title" className="text-lg font-semibold text-brand-100">
              {title}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-brand-400">{description}</p>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button type="button" onClick={onCancel} className="btn-ghost px-4 py-2 text-sm">
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={
              destructive
                ? "inline-flex items-center rounded-lg border border-rose-500/40 bg-rose-950/40 px-4 py-2 text-sm text-rose-100 transition hover:bg-rose-900/50"
                : "btn-primary px-4 py-2 text-sm"
            }
          >
            {confirmLabel}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
