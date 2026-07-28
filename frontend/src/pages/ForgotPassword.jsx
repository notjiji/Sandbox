import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Mail, ArrowLeft } from "lucide-react";
import AuthLayout from "../components/AuthLayout";

export default function ForgotPassword() {
  const handleSubmit = (e) => {
    e.preventDefault();
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
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="email" className="terminal-text mb-2 block">
            email_addr
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            placeholder="operator@domain.io"
            className="input-field"
          />
        </div>

        <p className="rounded-lg border border-brand-800/50 bg-brand-950/40 p-3 text-xs text-brand-500">
          {">"} recovery signal will be sent if the address exists in the database.
          no enumeration.
        </p>

        <motion.button
          type="submit"
          className="btn-primary w-full"
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
        >
          <Mail size={18} />
          Send Recovery Link
        </motion.button>
      </form>
    </AuthLayout>
  );
}
