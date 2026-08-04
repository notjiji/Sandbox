interface MemberAvatarProps {
  firstName?: string | null;
  lastName?: string | null;
  email: string;
  size?: "sm" | "md";
}

function initials(firstName?: string | null, lastName?: string | null, email?: string) {
  const first = firstName?.trim().charAt(0) ?? "";
  const last = lastName?.trim().charAt(0) ?? "";
  if (first || last) return `${first}${last}`.toUpperCase();
  return (email?.charAt(0) ?? "?").toUpperCase();
}

export default function MemberAvatar({
  firstName,
  lastName,
  email,
  size = "md",
}: MemberAvatarProps) {
  const sizeClass = size === "sm" ? "h-8 w-8 text-xs" : "h-10 w-10 text-sm";

  return (
    <div
      className={`flex shrink-0 items-center justify-center rounded-full border border-brand-600/50 bg-brand-900/50 font-semibold text-brand-200 ${sizeClass}`}
      aria-hidden
    >
      {initials(firstName, lastName, email)}
    </div>
  );
}
