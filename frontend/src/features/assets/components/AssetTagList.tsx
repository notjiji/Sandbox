interface AssetTagListProps {
  tags: string[];
  className?: string;
  maxVisible?: number;
}

export default function AssetTagList({
  tags,
  className = "",
  maxVisible = 4,
}: AssetTagListProps) {
  if (!tags.length) {
    return <span className="text-brand-600">—</span>;
  }

  const visible = tags.slice(0, maxVisible);
  const hiddenCount = tags.length - visible.length;

  return (
    <div className={`flex flex-wrap gap-1.5 ${className}`}>
      {visible.map((tag) => (
        <span
          key={tag}
          className="inline-flex rounded-full border border-brand-700/50 bg-brand-950/50 px-2 py-0.5 text-xs text-brand-300"
        >
          {tag}
        </span>
      ))}
      {hiddenCount > 0 && (
        <span className="inline-flex items-center px-1 text-xs text-brand-500">+{hiddenCount}</span>
      )}
    </div>
  );
}
