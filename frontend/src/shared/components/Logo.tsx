import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import GlitchText from "./GlitchText";

type LogoSize = "sm" | "md" | "lg";

interface LogoProps {
  size?: LogoSize;
}

const sizes: Record<LogoSize, string> = {
  sm: "text-xl",
  md: "text-2xl",
  lg: "text-4xl",
};

export default function Logo({ size = "md" }: LogoProps) {
  return (
    <Link to="/" className="group inline-flex items-center gap-2">
      <motion.span className="font-terminal text-brand-400" whileHover={{ scale: 1.05 }}>
        [//]
      </motion.span>
      <GlitchText
        text="SANDBOX"
        className={`font-dyslexic font-bold tracking-wider text-brand-200 ${sizes[size]}`}
      />
    </Link>
  );
}
