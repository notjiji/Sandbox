import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { LogOut, Settings, User } from "lucide-react";
import Logo from "@/shared/components/Logo";
import { authApi } from "@/features/auth/api";
import { tokenStorage } from "@/features/auth/storage";

export default function AppShell({ children, title, subtitle }) {
  const navigate = useNavigate();
  const isAuthenticated = tokenStorage.isAuthenticated();

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      tokenStorage.clear();
    }
    navigate("/login");
  };

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

      <motion.header
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 border-b border-brand-800/40 bg-void/60 backdrop-blur-sm"
      >
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo size="sm" />
          <nav className="flex items-center gap-2 sm:gap-3">
            {isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  className="btn-ghost inline-flex items-center gap-2 text-sm"
                >
                  <User size={16} />
                  Profile
                </Link>
                <Link
                  to="/settings"
                  className="btn-ghost inline-flex items-center gap-2 text-sm"
                >
                  <Settings size={16} />
                  Settings
                </Link>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="btn-ghost inline-flex items-center gap-2 text-sm"
                >
                  <LogOut size={16} />
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn-ghost text-sm">
                  Login
                </Link>
                <Link to="/register" className="btn-primary text-sm">
                  Register
                </Link>
              </>
            )}
          </nav>
        </div>
      </motion.header>

      <main className="relative z-10 mx-auto max-w-3xl px-6 py-12">
        {(title || subtitle) && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            {title && (
              <h1 className="text-3xl font-bold text-brand-50">{title}</h1>
            )}
            {subtitle && (
              <p className="mt-2 text-brand-400">{subtitle}</p>
            )}
          </motion.div>
        )}
        {children}
      </main>

      <footer className="relative z-10 border-t border-brand-900/40 py-6 text-center">
        <p className="terminal-text text-brand-600">
          sys.sandbox v1.0.0 // authenticated session
        </p>
      </footer>
    </div>
  );
}
