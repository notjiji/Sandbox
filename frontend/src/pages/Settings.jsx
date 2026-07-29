import { useState } from "react";
import { motion } from "framer-motion";
import { KeyRound } from "lucide-react";
import AppShell from "../components/AppShell";
import FormAlert from "../components/FormAlert";
import FormError from "../components/FormError";
import { authApi, ApiError } from "../lib/api";
import { validateChangePasswordForm } from "../lib/validation";

export default function Settings() {
  const [form, setForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

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

  return (
    <AppShell
      title="Settings"
      subtitle="Manage security preferences for your account."
    >
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-8 shadow-glow-lg"
      >
        <div className="mb-6 border-b border-brand-800/50 pb-4">
          <p className="terminal-text text-brand-500">{">"} security_config.ini</p>
          <h2 className="mt-2 text-xl font-bold text-brand-100">Change Password</h2>
          <p className="mt-1 text-sm text-brand-400">
            Update your pass key. You will stay signed in on this device.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          {alert && <FormAlert message={alert} />}
          {success && <FormAlert message={success} variant="success" />}

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
