import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { KeyRound } from "lucide-react";
import AuthLayout from "../components/AuthLayout";
import FormAlert from "../components/FormAlert";
import FormError from "../components/FormError";
import { authApi, ApiError } from "../lib/api";
import { validateResetPasswordForm } from "../lib/validation";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [form, setForm] = useState({ password: "", confirmPassword: "" });
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
    if (!token) {
      setAlert("Reset token is missing or invalid.");
      return;
    }

    const validationErrors = validateResetPasswordForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    try {
      const response = await authApi.resetPassword({
        token,
        new_password: form.password,
      });
      setSuccess(response.message ?? "Password reset successfully");
      setTimeout(() => navigate("/login"), 1500);
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
    <AuthLayout
      title="Set New Password"
      subtitle="Enter a new pass key for your operator account."
      footer={
        <Link to="/login" className="link-glow">
          Back to sign in
        </Link>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {alert && <FormAlert message={alert} />}
        {success && <FormAlert message={success} variant="success" />}

        <div>
          <label htmlFor="password" className="terminal-text mb-2 block">
            new_pass_key
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={handleChange}
            placeholder="StrongPassword123!"
            className="input-field"
          />
          <FormError message={errors.password} />
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
            placeholder="repeat pass key"
            className="input-field"
          />
          <FormError message={errors.confirmPassword} />
        </div>

        <motion.button
          type="submit"
          disabled={loading || !token}
          className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-60"
          whileHover={{ scale: loading ? 1 : 1.01 }}
          whileTap={{ scale: loading ? 1 : 0.98 }}
        >
          <KeyRound size={18} />
          {loading ? "Updating..." : "Update Password"}
        </motion.button>
      </form>
    </AuthLayout>
  );
}
