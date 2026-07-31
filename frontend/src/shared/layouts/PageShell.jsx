import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Logo from "@/shared/components/Logo";

export default function PageShell({ children, showNav = true }) {
  return (
    <div className="crt-vignette scanlines noise-bg relative min-h-screen overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(rgba(162,98,162,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(162,98,162,0.08) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {showNav && (
        <motion.header
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative z-10 border-b border-brand-800/40 bg-void/60 backdrop-blur-sm"
        >
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Logo size="sm" />
            <nav className="flex items-center gap-3">
              <Link to="/login" className="btn-ghost text-sm">
                Login
              </Link>
              <Link to="/register" className="btn-primary text-sm">
                Register
              </Link>
            </nav>
          </div>
        </motion.header>
      )}

      <main className="relative z-10">{children}</main>

      <footer className="relative z-10 border-t border-brand-900/40 py-6 text-center">
        <p className="terminal-text text-brand-600">
          sys.sandbox v1.0.0 // terminal mode active
        </p>
      </footer>
    </div>
  );
}
