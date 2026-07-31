import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { FolderKanban, Shield, Users } from "lucide-react";
import DashboardShell from "../components/DashboardShell";

const cards = [
  {
    title: "Projects",
    description: "Manage security projects, assets, and scans.",
    to: "/projects",
    icon: FolderKanban,
  },
  {
    title: "Members",
    description: "Invite teammates and manage organization roles.",
    to: "/organization/members",
    icon: Users,
  },
  {
    title: "Organization",
    description: "Update company profile and workspace settings.",
    to: "/organization/settings",
    icon: Shield,
  },
];

export default function Dashboard() {
  return (
    <DashboardShell
      title="Dashboard"
      subtitle="Overview of your organization workspace."
    >
      <div className="grid gap-6 md:grid-cols-3">
        {cards.map(({ title, description, to, icon: Icon }, index) => (
          <motion.div
            key={to}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Link
              to={to}
              className="glass-panel block h-full p-6 transition hover:border-brand-500/40"
            >
              <Icon size={24} className="mb-4 text-brand-400" />
              <h2 className="text-xl font-semibold text-brand-100">{title}</h2>
              <p className="mt-2 text-sm text-brand-500">{description}</p>
            </Link>
          </motion.div>
        ))}
      </div>
    </DashboardShell>
  );
}
