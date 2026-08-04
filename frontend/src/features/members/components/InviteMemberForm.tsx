import { Mail, UserPlus } from "lucide-react";
import FormError from "@/shared/components/FormError";
import type { ValidationErrors } from "@/shared/types/api";
import type { RoleInfo } from "@/shared/types/member";
import type { OrganizationRole } from "@/shared/types/organization";

interface InviteForm {
  email: string;
  role: OrganizationRole;
}

interface InviteMemberFormProps {
  form: InviteForm;
  roles: RoleInfo[];
  errors: ValidationErrors;
  inviting: boolean;
  onChange: (form: InviteForm) => void;
  onSubmit: (event: React.FormEvent) => void;
}

export default function InviteMemberForm({
  form,
  roles,
  errors,
  inviting,
  onChange,
  onSubmit,
}: InviteMemberFormProps) {
  return (
    <form onSubmit={onSubmit} className="glass-panel h-fit space-y-4 p-6">
      <h2 className="text-lg font-semibold text-brand-100">Invite member</h2>
      <p className="text-sm text-brand-500">
        Invites work for existing and new users. An email will be sent with a secure link.
      </p>

      <div>
        <label htmlFor="email" className="terminal-text mb-2 block">
          email_addr
        </label>
        <input
          id="email"
          name="email"
          type="email"
          value={form.email}
          onChange={(e) => onChange({ ...form, email: e.target.value })}
          className="input-field"
          placeholder="teammate@company.com"
        />
        <FormError message={errors.email} />
      </div>

      <div>
        <label htmlFor="role" className="terminal-text mb-2 block">
          role
        </label>
        <select
          id="role"
          name="role"
          value={form.role}
          onChange={(e) => onChange({ ...form, role: e.target.value as OrganizationRole })}
          className="input-field"
        >
          {roles
            .filter((role) => role.role !== "owner")
            .map((role) => (
              <option key={role.role} value={role.role}>
                {role.role.replace(/_/g, " ")}
              </option>
            ))}
        </select>
      </div>

      <button
        type="submit"
        disabled={inviting}
        className="btn-primary inline-flex w-full items-center justify-center gap-2"
      >
        <UserPlus size={18} />
        {inviting ? "Sending..." : "Send invitation"}
      </button>

      <p className="flex items-start gap-2 text-xs text-brand-600">
        <Mail size={14} className="mt-0.5 shrink-0" />
        Recipients without an account can register using the invite link.
      </p>
    </form>
  );
}

export type { InviteForm };
