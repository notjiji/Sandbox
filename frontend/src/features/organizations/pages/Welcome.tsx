import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Building2, Sparkles } from "lucide-react";
import AuthLayout from "@/shared/layouts/AuthLayout";
import { ROLE_LABELS } from "@/shared/types/member";
import type { OrganizationRole } from "@/shared/types/organization";
import { orgStorage } from "@/features/organizations/storage";

export default function Welcome() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const orgId = searchParams.get("org") ?? "";
  const orgName = searchParams.get("name") ?? "your organization";
  const orgSlug = searchParams.get("slug") ?? "";
  const role = (searchParams.get("role") ?? "viewer") as OrganizationRole;

  const handleContinue = () => {
    if (orgId) orgStorage.setActiveOrgId(orgId);
    navigate("/dashboard");
  };

  return (
    <AuthLayout
      title="Welcome aboard"
      subtitle="Your workspace is ready. Here is what happens next."
    >
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel space-y-6 p-8"
      >
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-brand-600/50 bg-brand-900/50 text-brand-200">
            <Building2 size={22} />
          </div>
          <div>
            <p className="terminal-text text-brand-500">{">"} workspace.joined</p>
            <h2 className="mt-2 text-2xl font-bold text-brand-100">{orgName}</h2>
            {orgSlug && <p className="mt-1 text-sm text-brand-500">{orgSlug}</p>}
            <p className="mt-3 text-brand-400">
              You joined as <strong>{ROLE_LABELS[role] ?? role.replace(/_/g, " ")}</strong>.
            </p>
          </div>
        </div>

        <ul className="space-y-3 rounded-lg border border-brand-800/50 bg-brand-950/30 p-4 text-sm text-brand-300">
          <li className="flex items-start gap-2">
            <Sparkles size={16} className="mt-0.5 shrink-0 text-brand-400" />
            Review your organization dashboard and security posture.
          </li>
          <li className="flex items-start gap-2">
            <Sparkles size={16} className="mt-0.5 shrink-0 text-brand-400" />
            Explore projects, assets, and scan results with your team.
          </li>
          <li className="flex items-start gap-2">
            <Sparkles size={16} className="mt-0.5 shrink-0 text-brand-400" />
            Update your profile and notification preferences anytime.
          </li>
        </ul>

        <button
          type="button"
          onClick={handleContinue}
          className="btn-primary inline-flex w-full items-center justify-center gap-2"
        >
          Enter workspace
          <ArrowRight size={18} />
        </button>

        <p className="text-center text-sm text-brand-500">
          Need another workspace?{" "}
          <Link to="/select-organization" className="link-glow">
            Switch organization
          </Link>
        </p>
      </motion.div>
    </AuthLayout>
  );
}
