import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { LogIn } from "lucide-react";
import AuthLayout from "../components/AuthLayout";
import FormAlert from "../components/FormAlert";
import FormError from "../components/FormError";
import { authApi, ApiError } from "../lib/api";
import { validateLoginForm } from "../lib/validation";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from ?? "/profile";
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
