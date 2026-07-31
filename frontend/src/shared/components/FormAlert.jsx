import { motion } from "framer-motion";

export default function FormAlert({ message, variant = "error" }) {
  if (!message) return null;

  const styles =
    variant === "success"
      ? "border-brand-500/40 bg-brand-950/50 text-brand-200"
      : "border-red-500/40 bg-red-950/30 text-red-300";

  return (
    <motion.p
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-lg border p-3 text-sm ${styles}`}
      role="alert"
    >
      {message}
    </motion.p>
  );
}
