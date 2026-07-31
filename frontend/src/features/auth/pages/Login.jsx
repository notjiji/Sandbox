import { useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { LogIn } from "lucide-react";
import AuthLayout from "@/shared/layouts/AuthLayout";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError } from "@/shared/api/client";
import { authApi } from "../api";
import { organizationsApi } from "@/features/organizations/api";
import { getActiveOrganizations, resolveActiveOrganization } from "@/features/organizations/org";
import { validateLoginForm } from "@/shared/lib/validation";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const redirectTo =
    searchParams.get("from") || location.state?.from || "/dashboard";
  const sessionExpired = searchParams.get("reason") === "session-expired";
  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setAlert("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateLoginForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    try {
      await authApi.login({
        email: form.email.trim().toLowerCase(),
        password: form.password,
      });
      try {
        const organizations = await organizationsApi.listMine();
        const activeOrgs = getActiveOrganizations(organizations);
        if (activeOrgs.length === 0) {
          navigate("/select-organization");
          return;
        }
        resolveActiveOrganization(organizations);
      } catch {
        // Org context is optional until the user joins or creates one.
      }
      navigate(redirectTo);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.code === "EMAIL_NOT_VERIFIED") {
          navigate(
            `/verify-email?email=${encodeURIComponent(form.email.trim().toLowerCase())}`,
          );
          return;
        }
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
      title="Sign In"
      subtitle="Authenticate to access the sandbox terminal."
      footer={
        <>
          No account?{" "}
          <Link to="/register" className="link-glow">
            Register here
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {sessionExpired && (
          <FormAlert message="Your session expired. Please sign in again." />
        )}
        {alert && <FormAlert message={alert} />}

        <div>
          <label htmlFor="email" className="terminal-text mb-2 block">
            email_addr
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={handleChange}
            placeholder="operator@domain.io"
            className="input-field"
          />
          <FormError message={errors.email} />
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <label htmlFor="password" className="terminal-text">
              pass_key
            </label>
            <Link to="/forgot-password" className="text-xs text-brand-500 hover:text-brand-300">
              forgot?
            </Link>
          </div>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={form.password}
            onChange={handleChange}
            placeholder="••••••••"
            className="input-field"
          />
          <FormError message={errors.password} />
        </div>

        <motion.button
          type="submit"
          disabled={loading}
          className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-60"
          whileHover={{ scale: loading ? 1 : 1.01 }}
          whileTap={{ scale: loading ? 1 : 0.98 }}
        >
          <LogIn size={18} />
          {loading ? "Authenticating..." : "Authenticate"}
        </motion.button>
      </form>
    </AuthLayout>
  );
}
