import { useState } from "react";
import { Building2 } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface OrganizationLogoProps {
  name: string;
  logoUrl?: string | null;
  size?: "xs" | "sm" | "md" | "lg";
  className?: string;
}

const sizeClass: Record<NonNullable<OrganizationLogoProps["size"]>, string> = {
  xs: "h-6 w-6 text-[10px] rounded-md",
  sm: "h-8 w-8 text-sm rounded-lg",
  md: "h-10 w-10 text-base rounded-lg",
  lg: "h-14 w-14 text-xl rounded-xl",
};

export default function OrganizationLogo({
  name,
  logoUrl,
  size = "sm",
  className,
}: OrganizationLogoProps) {
  const [imageError, setImageError] = useState(false);
  const initial = name.charAt(0).toUpperCase() || "?";
  const dimension = sizeClass[size];
  const showImage = logoUrl && !imageError;

  if (showImage) {
    return (
      <img
        src={logoUrl}
        alt={`${name} logo`}
        className={cn(
          "shrink-0 border border-brand-700/50 object-cover bg-brand-950/50",
          dimension,
          className,
        )}
        onError={() => setImageError(true)}
      />
    );
  }

  return (
    <span
      className={cn(
        "flex shrink-0 items-center justify-center border border-brand-600/50 bg-brand-900/60 font-semibold text-brand-200",
        dimension,
        className,
      )}
      aria-hidden
    >
      {initial !== "?" ? initial : <Building2 size={size === "xs" ? 12 : size === "lg" ? 22 : 16} />}
    </span>
  );
}
