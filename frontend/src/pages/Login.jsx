import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { LogIn } from "lucide-react";
import AuthLayout from "../components/AuthLayout";

export default function Login() {
  const handleSubmit = (e) => {
    e.preventDefault();
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
            required
            placeholder="••••••••"
            className="input-field"
          />
        </div>

        <motion.button
          type="submit"
          className="btn-primary w-full"
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
        >
          <LogIn size={18} />
          Authenticate
        </motion.button>
      </form>
    </AuthLayout>
  );
}
