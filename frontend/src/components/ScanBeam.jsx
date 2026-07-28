import { motion } from "framer-motion";

export default function ScanBeam() {
  return (
    <motion.div
      aria-hidden
      className="pointer-events-none fixed inset-x-0 top-0 z-40 h-24 bg-gradient-to-b from-brand-500/10 to-transparent"
      animate={{ y: ["-100%", "100vh"] }}
      transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
    />
  );
}
