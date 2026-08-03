import { ChevronLeft, ChevronRight } from "lucide-react";

interface AssetPaginationProps {
  page: number;
  limit: number;
  total: number;
  pageSizeOptions?: number[];
  onPageChange: (page: number) => void;
  onLimitChange?: (limit: number) => void;
}

export default function AssetPagination({
  page,
  limit,
  total,
  pageSizeOptions = [10, 20, 50],
  onPageChange,
  onLimitChange,
}: AssetPaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const canPrev = page > 1;
  const canNext = page < totalPages;
  const start = total === 0 ? 0 : (page - 1) * limit + 1;
  const end = Math.min(page * limit, total);

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-sm text-brand-500">
          Showing {start}–{end} of {total}
        </p>
        {onLimitChange && (
          <label className="flex items-center gap-2 text-sm text-brand-500">
            <span>Per page</span>
            <select
              value={limit}
              onChange={(e) => onLimitChange(Number(e.target.value))}
              className="input-field w-auto py-1.5 text-sm"
              aria-label="Items per page"
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={!canPrev}
          onClick={() => onPageChange(page - 1)}
          className="btn-ghost inline-flex items-center gap-1 disabled:opacity-40"
        >
          <ChevronLeft size={16} />
          Previous
        </button>
        <span className="px-3 text-sm text-brand-400">
          Page {page} of {totalPages}
        </span>
        <button
          type="button"
          disabled={!canNext}
          onClick={() => onPageChange(page + 1)}
          className="btn-ghost inline-flex items-center gap-1 disabled:opacity-40"
        >
          Next
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
