import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Logo from "./Logo";

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="crt-vignette scanlines noise-bg relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-15"
        style={{
          backgroundImage:
            "linear-gradient(rgba(162,98,162,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(162,98,162,0.1) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.45, ease: "easeOut" }}
        className="relative w-full max-w-md"
      >
        <div className="mb-8 text-center">
          <Logo size="md" />
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="terminal-text mt-4"
          >
            {">"} auth_module.exe
          </motion.p>
        </div>

        <div className="glass-panel animate-flicker p-8 shadow-glow-lg">
          <div className="mb-6 border-b border-brand-800/50 pb-4">
            <h1 className="text-2xl font-bold text-brand-100">{title}</h1>
            {subtitle && (
              <p className="mt-2 text-sm text-brand-400">{subtitle}</p>
            )}
          </div>

          {children}

          {footer && (
            <div className="mt-6 border-t border-brand-800/40 pt-4 text-center text-sm text-brand-400">
              {footer}
            </div>
          )}
        </div>

        <p className="terminal-text mt-6 text-center text-brand-700">
          <Link to="/" className="link-glow">
            {"<"} return_to_root
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
