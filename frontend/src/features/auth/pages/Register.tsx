import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { UserPlus } from "lucide-react";
import AuthLayout from "@/shared/layouts/AuthLayout";
import FormAlert from "@/shared/components/FormAlert";
import FormError from "@/shared/components/FormError";
import { ApiError } from "@/shared/api/client";
import type { FieldValidationDetail, ValidationErrors } from "@/shared/types/api";
import { authApi } from "../api";
import { validateRegisterForm } from "@/shared/lib/validation";
import { buildWelcomePath } from "@/shared/lib/welcome";
import { orgStorage } from "@/features/organizations/storage";

interface RegisterForm {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

function mapRegisterFieldErrors(details: unknown): ValidationErrors {
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
          : detail.field === "confirm_password"
            ? "confirmPassword"
            : detail.field;
    fieldErrors[key] = detail.message;
  }
  return fieldErrors;
}

export default function Register() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const inviteToken = searchParams.get("invite") ?? undefined;
  const prefilledEmail = searchParams.get("email") ?? "";
  const isInviteRegistration = Boolean(inviteToken);
  const [form, setForm] = useState<RegisterForm>({
    firstName: "",
    lastName: "",
    email: prefilledEmail,
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [alert, setAlert] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

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
    const validationErrors = validateRegisterForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    try {
      const response = await authApi.register({
        first_name: form.firstName.trim(),
        last_name: form.lastName.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
        invite_token: inviteToken,
      });
      setSuccess(response.message ?? "Account created successfully");

      const verifyParams = new URLSearchParams({
        email: form.email.trim().toLowerCase(),
      });
      if (response.organization) {
        orgStorage.setActiveOrgId(response.organization.id);
        verifyParams.set(
          "welcome",
          buildWelcomePath({
            id: response.organization.id,
            name: response.organization.name,
            slug: response.organization.slug,
            role: response.organization.role,
          }),
        );
      }

      setTimeout(() => navigate(`/verify-email?${verifyParams.toString()}`), 800);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.details) {
          setErrors(mapRegisterFieldErrors(error.details));
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
      title={isInviteRegistration ? "Join Organization" : "Create Account"}
      subtitle={
        isInviteRegistration
          ? "Create your account and choose a password to join the workspace."
          : "Register a new operator identity in the system."
      }
      footer={
        <>
          Already registered?{" "}
          <Link to="/login" className="link-glow">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {alert && <FormAlert message={alert} />}
        {success && <FormAlert message={success} variant="success" />}

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
              placeholder="John"
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
              placeholder="Doe"
              className="input-field"
            />
            <FormError message={errors.lastName} />
          </div>
        </div>

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
            readOnly={isInviteRegistration}
            placeholder="john@company.com"
            className="input-field read-only:cursor-not-allowed read-only:opacity-80"
          />
          <FormError message={errors.email} />
        </div>

        <div>
          <label htmlFor="password" className="terminal-text mb-2 block">
            pass_key
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={handleChange}
            placeholder="StrongPassword123! (min 12 chars)"
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
          disabled={loading}
          className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-60"
          whileHover={{ scale: loading ? 1 : 1.01 }}
          whileTap={{ scale: loading ? 1 : 0.98 }}
        >
          <UserPlus size={18} />
          {loading ? "Initializing..." : isInviteRegistration ? "Create account and join" : "Initialize Account"}
        </motion.button>
      </form>
    </AuthLayout>
  );
}
