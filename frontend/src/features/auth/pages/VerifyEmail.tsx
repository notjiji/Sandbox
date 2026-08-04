import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { MailCheck, RefreshCw } from "lucide-react";
import AuthLayout from "@/shared/layouts/AuthLayout";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError } from "@/shared/api/client";
import type { ValidationErrors } from "@/shared/types/api";
import { authApi } from "../api";
import { validateOtpForm, validateResendVerificationForm } from "@/shared/lib/validation";

export default function VerifyEmail() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialEmail = searchParams.get("email") ?? "";
  const welcomeRedirect = searchParams.get("welcome") ?? "";

  const [email, setEmail] = useState(initialEmail);
  const [otp, setOtp] = useState("");
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const otpInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    otpInputRef.current?.focus();
  }, []);

  const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, "").slice(0, 6);
    setOtp(value);
    setErrors((prev) => {
      const next = { ...prev };
      delete next.otp;
      return next;
    });
    setAlert("");
    setSuccess("");
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    setErrors((prev) => {
      const next = { ...prev };
      delete next.email;
      return next;
    });
    setAlert("");
    setSuccess("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErrors = validateOtpForm({ email, otp });
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    try {
      const response = await authApi.verifyEmail({
        email: email.trim().toLowerCase(),
        otp,
      });
      setSuccess(response.message ?? "Email verified successfully");
      const loginTarget = welcomeRedirect
        ? `/login?from=${encodeURIComponent(welcomeRedirect)}`
        : "/login";
      setTimeout(() => navigate(loginTarget), 1500);
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

  const handleResend = async () => {
    const validationErrors = validateResendVerificationForm({ email });
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setResending(true);
    setAlert("");
    try {
      const response = await authApi.resendVerification({
        email: email.trim().toLowerCase(),
      });
      setSuccess(response.message ?? "A new code has been sent if the account is unverified.");
    } catch (error) {
      if (error instanceof ApiError) {
        setAlert(error.message);
      } else {
        setAlert("Unable to reach the server. Try again later.");
      }
    } finally {
      setResending(false);
    }
  };

  return (
    <AuthLayout
      title="Verify Email"
      subtitle="Enter the 6-digit code sent to your inbox."
      footer={
        <>
          Already verified?{" "}
          <Link to="/login" className="link-glow">
            Sign in
          </Link>
        </>
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
            value={email}
            onChange={handleEmailChange}
            placeholder="operator@domain.io"
            className="input-field"
          />
          <FormError message={errors.email} />
        </div>

        <div>
          <label htmlFor="otp" className="terminal-text mb-2 block">
            verify_code
          </label>
          <input
            ref={otpInputRef}
            id="otp"
            name="otp"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            value={otp}
            onChange={handleOtpChange}
            placeholder="000000"
            className="input-field text-center text-2xl tracking-[0.5em]"
            maxLength={6}
          />
          <FormError message={errors.otp} />
        </div>

        <motion.button
          type="submit"
          disabled={loading}
          className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-60"
          whileHover={{ scale: loading ? 1 : 1.01 }}
          whileTap={{ scale: loading ? 1 : 0.98 }}
        >
          <MailCheck size={18} />
          {loading ? "Verifying..." : "Verify Email"}
        </motion.button>

        <motion.button
          type="button"
          onClick={handleResend}
          disabled={resending}
          className="btn-ghost w-full disabled:cursor-not-allowed disabled:opacity-60"
          whileHover={{ scale: resending ? 1 : 1.01 }}
          whileTap={{ scale: resending ? 1 : 0.98 }}
        >
          <RefreshCw size={16} className={resending ? "animate-spin" : ""} />
          {resending ? "Sending..." : "Resend Code"}
        </motion.button>
      </form>
    </AuthLayout>
  );
}
