import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { AlertTriangle, Home } from "lucide-react";
import GlitchText from "@/shared/components/GlitchText";

export default function NotFound() {
  return (
    <div className="crt-vignette scanlines noise-bg relative flex min-h-screen flex-col items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="text-center"
      >
        <motion.div
          animate={{ rotate: [0, -2, 2, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="mx-auto mb-6 inline-flex rounded-full border border-brand-600/50 bg-brand-900/30 p-5 text-brand-400 shadow-glow"
        >
          <AlertTriangle size={40} />
        </motion.div>

        <p className="terminal-text mb-2">ERROR_CODE: 0x404</p>

        <h1 className="text-6xl font-bold text-brand-200 md:text-8xl">
          <GlitchText text="404" />
        </h1>

        <p className="mt-4 text-lg text-brand-400">
          Signal lost. The requested route does not exist in this dimension.
        </p>

        <div className="glass-panel mt-8 max-w-md p-4 font-terminal text-left text-sm text-brand-500">
          <p>$ cd /requested/path</p>
          <p className="mt-1 text-brand-600">
            bash: cd: /requested/path: No such file or directory
          </p>
          <p className="mt-2 animate-blink text-brand-400">$ _</p>
        </div>

        <Link to="/" className="btn-primary mt-8 inline-flex">
          <Home size={18} />
          Return Home
        </Link>
      </motion.div>
    </div>
  );
}
