import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Mail, ArrowLeft } from "lucide-react";
import AuthLayout from "@/shared/layouts/AuthLayout";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError } from "@/shared/api/client";
import { authApi } from "../api";
import { validateForgotPasswordForm } from "@/shared/lib/validation";

export default function ForgotPassword() {
  const [form, setForm] = useState({ email: "" });
  const [errors, setErrors] = useState({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ email: e.target.value });
    setErrors({});
    setAlert("");
    setSuccess("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateForgotPasswordForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    try {
      const response = await authApi.forgotPassword(form);
      setSuccess(response.message ?? "If the email exists, a recovery link will be sent.");
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
      title="Reset Password"
      subtitle="We'll transmit a recovery link to your registered email."
      footer={
        <Link to="/login" className="link-glow inline-flex items-center gap-1">
          <ArrowLeft size={14} />
          Back to sign in
        </Link>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {alert && <FormAlert message={alert} />}
        {success && <FormAlert message={success} variant="success" />}

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

        <p className="rounded-lg border border-brand-800/50 bg-brand-950/40 p-3 text-xs text-brand-500">
          {">"} recovery signal will be sent if the address exists in the database.
          no enumeration.
        </p>

        <motion.button
          type="submit"
          disabled={loading}
          className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-60"
          whileHover={{ scale: loading ? 1 : 1.01 }}
          whileTap={{ scale: loading ? 1 : 0.98 }}
        >
          <Mail size={18} />
          {loading ? "Transmitting..." : "Send Recovery Link"}
        </motion.button>
      </form>
    </AuthLayout>
  );
}
