import { motion } from "framer-motion";
import type { ElementType, HTMLAttributes } from "react";
import { cn } from "@/shared/lib/utils";

interface GlitchTextProps extends HTMLAttributes<HTMLElement> {
  text: string;
  as?: ElementType;
  className?: string;
}

export default function GlitchText({
  text,
  as: Tag = "span",
  className,
  ...props
}: GlitchTextProps) {
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
