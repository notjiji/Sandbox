import { Search } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface ListSearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export default function ListSearchBar({
  value,
  onChange,
  placeholder = "Search...",
  className,
}: ListSearchBarProps) {
  return (
    <div className={cn("relative", className)}>
      <Search
        size={16}
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-brand-500"
      />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input-field pl-9"
        placeholder={placeholder}
        aria-label={placeholder}
      />
    </div>
  );
}
