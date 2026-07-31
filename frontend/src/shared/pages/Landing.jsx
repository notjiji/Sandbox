import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Shield, Terminal, Zap } from "lucide-react";
import PageShell from "@/shared/layouts/PageShell";
import GlitchText from "@/shared/components/GlitchText";
import ScanBeam from "@/shared/components/ScanBeam";

const features = [
  {
    icon: Shield,
    title: "Secure Scanning",
    desc: "Probe systems without leaving traces in the void.",
  },
  {
    icon: Terminal,
    title: "Terminal Control",
    desc: "Computer-native interface for operators who think in code.",
  },
  {
    icon: Zap,
    title: "Real-time Signal",
    desc: "Watch vulnerabilities surface as the scan propagates.",
  },
];

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.12 },
  },
};

const item = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0 },
};

export default function Landing() {
  return (
    <PageShell>
      <ScanBeam />

      <section className="mx-auto max-w-6xl px-6 py-20 md:py-28">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          <p className="terminal-text mb-4 animate-pulse-glow inline-block rounded border border-brand-700/50 bg-brand-950/50 px-4 py-1">
            {">"} initializing sandbox environment...
            <span className="animate-blink ml-1 inline-block">_</span>
          </p>

          <h1 className="mt-6 text-4xl font-bold leading-tight text-brand-50 md:text-6xl">
            <GlitchText text="Security" className="text-brand-200" />
            <br />
            <span className="text-brand-400">in the machine.</span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-brand-300/90">
            A glitchy, computer-native platform for scanning assets and
            surfacing risk. Built for operators who live in the terminal.
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link to="/register">
              <motion.span
                className="btn-primary text-base"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
              >
                Get Started
              </motion.span>
            </Link>
            <Link to="/login" className="btn-ghost text-base">
              Sign In
            </Link>
          </div>
        </motion.div>

        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="mt-24 grid gap-6 md:grid-cols-3"
        >
          {features.map(({ icon: Icon, title, desc }) => (
            <motion.div
              key={title}
              variants={item}
              whileHover={{ y: -4, boxShadow: "0 0 30px rgba(162,98,162,0.25)" }}
              className="glass-panel group p-6 transition-shadow"
            >
              <div className="mb-4 inline-flex rounded-lg border border-brand-600/40 bg-brand-900/30 p-3 text-brand-300 group-hover:shadow-glow">
                <Icon size={22} />
              </div>
              <h3 className="text-lg font-bold text-brand-100">{title}</h3>
              <p className="mt-2 text-sm text-brand-400">{desc}</p>
              <p className="terminal-text mt-4 text-brand-600 opacity-0 transition-opacity group-hover:opacity-100">
                {">"} module loaded
              </p>
            </motion.div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="glass-panel mt-16 overflow-hidden p-6 font-terminal text-sm text-brand-400"
        >
          <p className="text-brand-500">$ sandbox --status</p>
          <p className="mt-2 text-brand-300">
            [<span className="text-brand-400">OK</span>] core online
          </p>
          <p className="text-brand-300">
            [<span className="text-brand-400">OK</span>] auth module standby
          </p>
          <p className="text-brand-300">
            [<span className="text-brand-400">OK</span>] workspace ready
          </p>
          <p className="mt-2 animate-blink text-brand-500">$ _</p>
        </motion.div>
      </section>
    </PageShell>
  );
}
