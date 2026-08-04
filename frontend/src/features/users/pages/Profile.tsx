import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { BadgeCheck, Building2, Mail, Save, Shield } from "lucide-react";
import AppShell from "@/shared/layouts/AppShell";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError } from "@/shared/api/client";
import type { FieldValidationDetail, ValidationErrors } from "@/shared/types/api";
import type { UserProfile } from "@/shared/types/user";
import { usersApi } from "../api";
import { validateProfileForm } from "@/shared/lib/validation";

interface ProfileForm {
  firstName: string;
  lastName: string;
}

function ProfileSkeleton() {
  return (
    <div className="glass-panel animate-pulse space-y-4 p-8">
      <div className="h-6 w-48 rounded bg-brand-900/60" />
      <div className="h-4 w-full rounded bg-brand-900/40" />
      <div className="h-4 w-3/4 rounded bg-brand-900/40" />
      <div className="h-4 w-2/3 rounded bg-brand-900/40" />
    </div>
  );
}

function mapProfileFieldErrors(details: unknown): ValidationErrors {
  if (!Array.isArray(details)) return {};
  const fieldErrors: ValidationErrors = {};
  for (const item of details) {
    const detail = item as FieldValidationDetail;
    if (typeof detail.field !== "string" || typeof detail.message !== "string") continue;
    const key =
      detail.field === "first_name"
        ? "firstName"
        : detail.field === "last_name"
          ? "lastName"
          : detail.field;
    fieldErrors[key] = detail.message;
  }
  return fieldErrors;
}

export default function Profile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [form, setForm] = useState<ProfileForm>({ firstName: "", lastName: "" });
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadProfile() {
      try {
        const data = await usersApi.getMe();
        if (!active) return;
        setProfile(data);
        setForm({
          firstName: data.first_name,
          lastName: data.last_name,
        });
      } catch (error) {
        if (!active) return;
        if (error instanceof ApiError) {
          setAlert(error.message);
        } else {
          setAlert("Unable to load profile.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadProfile();
    return () => {
      active = false;
    };
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[name];
      return next;
    });
    setAlert("");
    setSuccess("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErrors = validateProfileForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setSaving(true);
    try {
      const updated = await usersApi.updateMe({
          first_name: form.firstName.trim(),
          last_name: form.lastName.trim(),
        });
      setProfile(updated);
      setForm({
        firstName: updated.first_name,
        lastName: updated.last_name,
      });
      setSuccess("Profile updated successfully.");
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.details) {
          setErrors(mapProfileFieldErrors(error.details));
        }
        setAlert(error.message);
      } else {
        setAlert("Unable to update profile.");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell title="Profile" subtitle="Your operator identity in the sandbox.">
      {alert && <FormAlert message={alert} />}
      {success && <FormAlert message={success} variant="success" />}
      {loading && <ProfileSkeleton />}

      {!loading && profile && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-8 shadow-glow-lg"
        >
          <div className="mb-6 flex items-start justify-between gap-4 border-b border-brand-800/50 pb-6">
            <div>
              <p className="terminal-text text-brand-500">{">"} user_profile.sys</p>
              <h2 className="mt-2 text-2xl font-bold text-brand-100">
                {profile.first_name} {profile.last_name}
              </h2>
              <p className="mt-1 text-sm text-brand-500">ID: {profile.id}</p>
            </div>
            {profile.email_verified ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-green-500/30 bg-green-950/40 px-3 py-1 text-xs text-green-300">
                <BadgeCheck size={14} />
                verified
              </span>
            ) : (
              <Link
                to={`/verify-email?email=${encodeURIComponent(profile.email)}`}
                className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-950/40 px-3 py-1 text-xs text-amber-300 hover:text-amber-200"
              >
                verify email
              </Link>
            )}
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" noValidate>
            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <label htmlFor="firstName" className="terminal-text mb-2 block">
                  first_name
                </label>
                <input
                  id="firstName"
                  name="firstName"
                  type="text"
                  autoComplete="given-name"
                  value={form.firstName}
                  onChange={handleChange}
                  className="input-field"
                />
                <FormError message={errors.firstName} />
              </div>

              <div>
                <label htmlFor="lastName" className="terminal-text mb-2 block">
                  last_name
                </label>
                <input
                  id="lastName"
                  name="lastName"
                  type="text"
                  autoComplete="family-name"
                  value={form.lastName}
                  onChange={handleChange}
                  className="input-field"
                />
                <FormError message={errors.lastName} />
              </div>
            </div>

            <motion.button
              type="submit"
              disabled={saving}
              className="btn-primary disabled:cursor-not-allowed disabled:opacity-60"
              whileHover={{ scale: saving ? 1 : 1.01 }}
              whileTap={{ scale: saving ? 1 : 0.98 }}
            >
              <Save size={18} />
              {saving ? "Saving..." : "Save Profile"}
            </motion.button>
          </form>

          <dl className="mt-8 space-y-5 border-t border-brand-800/50 pt-6">
            <div className="flex items-center gap-3">
              <Mail size={18} className="text-brand-400" />
              <div>
                <dt className="terminal-text text-brand-600">email</dt>
                <dd className="text-brand-100">{profile.email}</dd>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Shield size={18} className="text-brand-400" />
              <div>
                <dt className="terminal-text text-brand-600">role</dt>
                <dd className="text-brand-100">—</dd>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Building2 size={18} className="text-brand-400" />
              <div>
                <dt className="terminal-text text-brand-600">organization</dt>
                <dd className="text-brand-100">—</dd>
              </div>
            </div>
          </dl>
        </motion.div>
      )}
    </AppShell>
  );
}
