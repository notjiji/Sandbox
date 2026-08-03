import { ListTree, Rows3 } from "lucide-react";

type ViewMode = "tree" | "flat";

interface AssetViewToggleProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
  treeAvailable: boolean;
}

export default function AssetViewToggle({ mode, onChange, treeAvailable }: AssetViewToggleProps) {
  return (
    <div className="flex items-center gap-1 rounded-lg border border-brand-800/50 p-1">
      <button
        type="button"
        disabled={!treeAvailable}
        onClick={() => onChange("tree")}
        className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition ${
          mode === "tree"
            ? "bg-brand-800/60 text-brand-100"
            : "text-brand-500 hover:text-brand-300"
        } disabled:cursor-not-allowed disabled:opacity-40`}
        title={
          treeAvailable
            ? "Paginate root assets and expand children"
            : "Tree view unavailable while searching or filtering child types"
        }
      >
        <ListTree size={16} />
        Tree
      </button>
      <button
        type="button"
        onClick={() => onChange("flat")}
        className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition ${
          mode === "flat"
            ? "bg-brand-800/60 text-brand-100"
            : "text-brand-500 hover:text-brand-300"
        }`}
      >
        <Rows3 size={16} />
        Flat
      </button>
    </div>
  );
}
