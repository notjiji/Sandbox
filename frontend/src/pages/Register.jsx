import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { UserPlus } from "lucide-react";
import AuthLayout from "../components/AuthLayout";
import FormAlert from "../components/FormAlert";
import FormError from "../components/FormError";
import { authApi, ApiError } from "../lib/api";
import { validateRegisterForm } from "../lib/validation";

export default function Register() {
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
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
    const validationErrors = validateRegisterForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    try {
      await authApi.register({
        full_name: form.fullName,
        email: form.email,
        password: form.password,
        confirm_password: form.confirmPassword,
      });
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.details?.length) {
          const fieldErrors = {};
          error.details.forEach(({ field, message }) => {
            const key = field === "full_name" ? "fullName" : field === "confirm_password" ? "confirmPassword" : field;
            fieldErrors[key] = message;
          });
          setErrors(fieldErrors);
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
      title="Create Account"
      subtitle="Register a new operator identity in the system."
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

        <div>
          <label htmlFor="fullName" className="terminal-text mb-2 block">
            display_name
          </label>
          <input
            id="fullName"
            name="fullName"
            type="text"
            autoComplete="name"
            value={form.fullName}
            onChange={handleChange}
            placeholder="Operator Zero"
            className="input-field"
          />
          <FormError message={errors.fullName} />
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
            placeholder="operator@domain.io"
            className="input-field"
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
            placeholder="min 8 characters"
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
          {loading ? "Initializing..." : "Initialize Account"}
        </motion.button>
      </form>
    </AuthLayout>
  );
}
