import { motion } from "framer-motion";
import { cn } from "../lib/utils";

export default function GlitchText({ text, as: Tag = "span", className, ...props }) {
  return (
    <Tag className={cn("glitch-text", className)} data-text={text} {...props}>
      <motion.span
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {text}
      </motion.span>
    </Tag>
  );
}
