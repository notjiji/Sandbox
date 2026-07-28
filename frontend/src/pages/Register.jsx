import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { UserPlus } from "lucide-react";
import AuthLayout from "../components/AuthLayout";

export default function Register() {
  const handleSubmit = (e) => {
    e.preventDefault();
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
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="fullName" className="terminal-text mb-2 block">
            display_name
          </label>
          <input
            id="fullName"
            name="fullName"
            type="text"
            autoComplete="name"
            required
            placeholder="Operator Zero"
            className="input-field"
          />
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
            required
            placeholder="operator@domain.io"
            className="input-field"
          />
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
            required
            minLength={8}
            placeholder="min 8 characters"
            className="input-field"
          />
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
            required
            minLength={8}
            placeholder="repeat pass key"
            className="input-field"
          />
        </div>

        <motion.button
          type="submit"
          className="btn-primary w-full"
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
        >
          <UserPlus size={18} />
          Initialize Account
        </motion.button>
      </form>
    </AuthLayout>
  );
}
