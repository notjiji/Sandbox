import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { KeyRound, LogOut, Monitor, ShieldOff } from "lucide-react";
import AppShell from "../components/AppShell";
import FormAlert from "../components/FormAlert";
import FormError from "../components/FormError";
import { authApi, ApiError } from "../lib/api";
import { tokenStorage } from "../lib/auth";
import { validateChangePasswordForm } from "../lib/validation";

function formatSessionTime(value) {
  if (!value) return "unknown";
  return new Date(value).toLocaleString();
}

function SessionSkeleton() {
  return (
    <div className="animate-pulse space-y-3">
      <div className="h-16 rounded bg-brand-900/40" />
      <div className="h-16 rounded bg-brand-900/40" />
    </div>
  );
}

export default function Settings() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [sessionActionId, setSessionActionId] = useState(null);
  const [bulkAction, setBulkAction] = useState(null);

  const loadSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const data = await authApi.listSessions();
      setSessions(data.items ?? []);
    } catch (error) {
      if (error instanceof ApiError) {
        setAlert(error.message);
      } else {
        setAlert("Unable to load active sessions.");
      }
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setAlert("");
    setSuccess("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateChangePasswordForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    try {
      const response = await authApi.changePassword({
        current_password: form.currentPassword,
        new_password: form.newPassword,
      });
      setSuccess(response.message ?? "Password changed successfully");
      setForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
      tokenStorage.clear();
      navigate("/login?reason=session-expired");
    } catch (error) {
      if (error instanceof ApiError) {
        setAlert(error.message);
      } else {
        setAlert("Unable to reach the server. Try again later.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId) => {
    setSessionActionId(sessionId);
    setAlert("");
    setSuccess("");
    try {
      const response = await authApi.revokeSession(sessionId);
      if (response.revoked_current_session) {
        tokenStorage.clear();
        navigate("/login?reason=session-expired");
        return;
      }
      setSuccess(response.message ?? "Session revoked.");
      await loadSessions();
    } catch (error) {
      if (error instanceof ApiError) {
        setAlert(error.message);
      } else {
        setAlert("Unable to revoke session.");
      }
    } finally {
      setSessionActionId(null);
    }
  };

  const handleRevokeOthers = async () => {
    setBulkAction("others");
    setAlert("");
    setSuccess("");
    try {
      const response = await authApi.revokeOtherSessions();
      setSuccess(response.message ?? "Other sessions signed out.");
      await loadSessions();
    } catch (error) {
      if (error instanceof ApiError) {
        setAlert(error.message);
      } else {
        setAlert("Unable to sign out other sessions.");
      }
    } finally {
      setBulkAction(null);
    }
  };

  const handleRevokeAll = async () => {
    setBulkAction("all");
    setAlert("");
    setSuccess("");
    try {
      await authApi.revokeAllSessions();
      tokenStorage.clear();
      navigate("/login?reason=session-expired");
    } catch (error) {
      if (error instanceof ApiError) {
        setAlert(error.message);
      } else {
        setAlert("Unable to sign out everywhere.");
      }
      setBulkAction(null);
    }
  };

  return (
    <AppShell
      title="Settings"
      subtitle="Manage security preferences for your account."
    >
      {alert && <div className="mb-6"><FormAlert message={alert} /></div>}
      {success && <div className="mb-6"><FormAlert message={success} variant="success" /></div>}

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel mb-8 p-8 shadow-glow-lg"
      >
        <div className="mb-6 border-b border-brand-800/50 pb-4">
          <p className="terminal-text text-brand-500">{">"} active_sessions.log</p>
          <h2 className="mt-2 text-xl font-bold text-brand-100">Active Sessions</h2>
          <p className="mt-1 text-sm text-brand-400">
            Devices and browsers currently signed in to your account.
          </p>
        </div>

        {sessionsLoading ? (
          <SessionSkeleton />
        ) : sessions.length === 0 ? (
          <p className="text-sm text-brand-400">No active sessions found.</p>
        ) : (
          <ul className="space-y-3">
            {sessions.map((session) => (
              <li
                key={session.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-brand-800/50 bg-brand-950/30 p-4"
              >
                <div className="flex items-start gap-3">
                  <Monitor size={18} className="mt-0.5 text-brand-400" />
                  <div>
                    <p className="font-medium text-brand-100">
                      {session.is_current ? "This device" : "Active session"}
                      {session.is_current && (
                        <span className="ml-2 text-xs text-green-300">current</span>
                      )}
                    </p>
                    <p className="terminal-text mt-1 text-xs text-brand-500">
                      started {formatSessionTime(session.created_at)}
                    </p>
                    <p className="terminal-text text-xs text-brand-600">
                      expires {formatSessionTime(session.expires_at)}
                    </p>
                  </div>
                </div>
                {!session.is_current && (
                  <motion.button
                    type="button"
                    onClick={() => handleRevokeSession(session.id)}
                    disabled={sessionActionId === session.id}
                    className="btn-ghost text-sm disabled:opacity-60"
                    whileTap={{ scale: 0.98 }}
                  >
                    {sessionActionId === session.id ? "Revoking..." : "Revoke"}
                  </motion.button>
                )}
              </li>
            ))}
          </ul>
        )}

        <div className="mt-6 flex flex-wrap gap-3 border-t border-brand-800/50 pt-6">
          <motion.button
            type="button"
            onClick={handleRevokeOthers}
            disabled={bulkAction !== null || sessions.length <= 1}
            className="btn-ghost inline-flex items-center gap-2 disabled:opacity-60"
            whileTap={{ scale: 0.98 }}
          >
            <ShieldOff size={16} />
            {bulkAction === "others" ? "Signing out..." : "Sign Out Other Devices"}
          </motion.button>
          <motion.button
            type="button"
            onClick={handleRevokeAll}
            disabled={bulkAction !== null}
            className="btn-ghost inline-flex items-center gap-2 text-red-300 hover:text-red-200 disabled:opacity-60"
            whileTap={{ scale: 0.98 }}
          >
            <LogOut size={16} />
            {bulkAction === "all" ? "Signing out..." : "Sign Out Everywhere"}
          </motion.button>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-8 shadow-glow-lg"
      >
        <div className="mb-6 border-b border-brand-800/50 pb-4">
          <p className="terminal-text text-brand-500">{">"} security_config.ini</p>
          <h2 className="mt-2 text-xl font-bold text-brand-100">Change Password</h2>
          <p className="mt-1 text-sm text-brand-400">
            Updates your pass key and signs you out of all devices.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <div>
            <label htmlFor="currentPassword" className="terminal-text mb-2 block">
              current_pass
            </label>
            <input
              id="currentPassword"
              name="currentPassword"
              type="password"
              autoComplete="current-password"
              value={form.currentPassword}
              onChange={handleChange}
              className="input-field"
            />
            <FormError message={errors.currentPassword} />
          </div>

          <div>
            <label htmlFor="newPassword" className="terminal-text mb-2 block">
              new_pass_key
            </label>
            <input
              id="newPassword"
              name="newPassword"
              type="password"
              autoComplete="new-password"
              value={form.newPassword}
              onChange={handleChange}
              placeholder="StrongPassword123!"
              className="input-field"
            />
            <FormError message={errors.newPassword} />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="terminal-text mb-2 block">
              confirm_pass
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              value={form.confirmPassword}
              onChange={handleChange}
              className="input-field"
            />
            <FormError message={errors.confirmPassword} />
          </div>

          <motion.button
            type="submit"
            disabled={loading}
            className="btn-primary disabled:cursor-not-allowed disabled:opacity-60"
            whileHover={{ scale: loading ? 1 : 1.01 }}
            whileTap={{ scale: loading ? 1 : 0.98 }}
          >
            <KeyRound size={18} />
            {loading ? "Updating..." : "Update Password"}
          </motion.button>
        </form>
      </motion.div>
    </AppShell>
  );
}
