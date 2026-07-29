import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { BadgeCheck, Building2, Mail, Shield } from "lucide-react";
import AppShell from "../components/AppShell";
import FormAlert from "../components/FormAlert";
import { authApi, ApiError } from "../lib/api";

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

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [alert, setAlert] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadProfile() {
      try {
        const data = await authApi.getMe();
        if (active) setProfile(data);
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

    loadProfile();
    return () => {
      active = false;
    };
  }, []);

  return (
    <AppShell
      title="Profile"
      subtitle="Your operator identity in the sandbox."
    >
      {alert && <FormAlert message={alert} />}
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
            {profile.is_verified ? (
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

          <dl className="space-y-5">
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
                <dd className="text-brand-100">{profile.role ?? "unassigned"}</dd>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Building2 size={18} className="text-brand-400" />
              <div>
                <dt className="terminal-text text-brand-600">organization</dt>
                <dd className="text-brand-100">{profile.organization ?? "none"}</dd>
              </div>
            </div>
          </dl>
        </motion.div>
      )}
    </AppShell>
  );
}
