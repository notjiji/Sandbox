import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertCircle,
  Ban,
  CheckCircle2,
  Clock,
  LogIn,
  UserPlus,
} from "lucide-react";
import AuthLayout from "@/shared/layouts/AuthLayout";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import { buildWelcomePath } from "@/shared/lib/welcome";
import type { InvitePreview } from "@/shared/types/member";
import { INVITE_STATUS_LABELS, ROLE_LABELS } from "@/shared/types/member";
import { membersApi } from "../api";
import { tokenStorage } from "@/features/auth/storage";
import { orgStorage } from "@/features/organizations/storage";

function InviteStatusPanel({
  preview,
  icon,
  title,
  description,
  action,
}: {
  preview: InvitePreview;
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel space-y-6 p-8"
    >
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-brand-700/50 bg-brand-950/50 text-brand-300">
          {icon}
        </div>
        <div>
          <p className="terminal-text text-brand-500">{">"} invite.sys // {preview.status}</p>
          <h2 className="mt-2 text-2xl font-bold text-brand-100">{title}</h2>
          <p className="mt-2 text-brand-400">{description}</p>
        </div>
      </div>

      <div className="rounded-lg border border-brand-800/50 bg-brand-950/30 p-4 text-sm text-brand-300">
        <p>
          <span className="text-brand-500">Organization:</span> {preview.organization_name}
        </p>
        <p className="mt-1">
          <span className="text-brand-500">Invited as:</span>{" "}
          {ROLE_LABELS[preview.role] ?? preview.role.replace(/_/g, " ")}
        </p>
        <p className="mt-1">
          <span className="text-brand-500">Status:</span>{" "}
          {INVITE_STATUS_LABELS[preview.status]}
        </p>
      </div>

      {action}
    </motion.div>
  );
}

export default function AcceptInvite() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [preview, setPreview] = useState<InvitePreview | null>(null);
  const [alert, setAlert] = useState("");
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);
  const isAuthenticated = tokenStorage.isAuthenticated();

  useEffect(() => {
    let active = true;

    async function loadPreview() {
      if (!token) {
        setAlert("Missing invitation token.");
        setLoading(false);
        return;
      }

      try {
        const data = await membersApi.previewInvite(token);
        if (active) setPreview(data);
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Invalid invitation.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadPreview();
    return () => {
      active = false;
    };
  }, [token]);

  const goToWelcome = (organization: {
    id: string;
    name: string;
    slug: string;
    role: string;
  }) => {
    orgStorage.setActiveOrgId(organization.id);
    navigate(
      buildWelcomePath({
        id: organization.id,
        name: organization.name,
        slug: organization.slug,
        role: organization.role,
      }),
    );
  };

  const handleAccept = async () => {
    if (!token) return;
    setAccepting(true);
    setAlert("");
    try {
      const organization = await membersApi.acceptInviteToken(token);
      goToWelcome(organization);
    } catch (error) {
      setAlert(error instanceof ApiError ? error.message : "Unable to accept invitation.");
    } finally {
      setAccepting(false);
    }
  };

  const registerHref = `/register?invite=${encodeURIComponent(token)}&email=${encodeURIComponent(preview?.email ?? "")}`;
  const loginHref = `/login?from=${encodeURIComponent("/accept-invite?token=" + token)}`;

  return (
    <AuthLayout
      title="Organization Invitation"
      subtitle="Review and accept your workspace invitation."
    >
      {alert && <FormAlert message={alert} />}

      {loading ? (
        <div className="glass-panel animate-pulse p-8">Loading invitation...</div>
      ) : preview?.status === "accepted" ? (
        <InviteStatusPanel
          preview={preview}
          icon={<CheckCircle2 size={20} className="text-emerald-400" />}
          title="Invitation already accepted"
          description="This invitation has already been used. Sign in to access your workspace."
          action={
            <Link to="/login" className="btn-primary inline-flex w-full items-center justify-center gap-2">
              <LogIn size={18} />
              Sign in
            </Link>
          }
        />
      ) : preview?.status === "expired" ? (
        <InviteStatusPanel
          preview={preview}
          icon={<Clock size={20} className="text-amber-400" />}
          title="Invitation expired"
          description="This link is no longer valid. Ask an organization administrator to resend your invitation."
          action={
            <Link to="/login" className="btn-ghost inline-flex w-full items-center justify-center gap-2">
              Sign in with existing account
            </Link>
          }
        />
      ) : preview?.status === "revoked" ? (
        <InviteStatusPanel
          preview={preview}
          icon={<Ban size={20} className="text-rose-400" />}
          title="Invitation revoked"
          description="An administrator revoked this invitation before it was accepted."
          action={
            <Link to="/login" className="btn-ghost inline-flex w-full items-center justify-center gap-2">
              Sign in with existing account
            </Link>
          }
        />
      ) : preview?.status === "pending" ? (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel space-y-6 p-8"
        >
          <div>
            <p className="terminal-text text-brand-500">{">"} invite.sys // pending</p>
            <h2 className="mt-2 text-2xl font-bold text-brand-100">{preview.organization_name}</h2>
            <p className="mt-2 text-brand-400">
              {preview.inviter_name} invited <strong>{preview.email}</strong> as{" "}
              <strong>{ROLE_LABELS[preview.role] ?? preview.role.replace(/_/g, " ")}</strong>.
            </p>
            <p className="mt-2 text-xs text-brand-600">
              Expires {new Date(preview.expires_at).toLocaleString()}
            </p>
          </div>

          {isAuthenticated ? (
            <button
              type="button"
              onClick={handleAccept}
              disabled={accepting}
              className="btn-primary inline-flex w-full items-center justify-center gap-2"
            >
              <CheckCircle2 size={18} />
              {accepting ? "Joining organization..." : "Accept and join organization"}
            </button>
          ) : (
            <div className="space-y-3">
              {preview.user_exists ? (
                <Link
                  to={loginHref}
                  className="btn-primary inline-flex w-full items-center justify-center gap-2"
                >
                  <LogIn size={18} />
                  Sign in to accept
                </Link>
              ) : (
                <Link
                  to={registerHref}
                  className="btn-primary inline-flex w-full items-center justify-center gap-2"
                >
                  <UserPlus size={18} />
                  Create account and choose password
                </Link>
              )}
              {!preview.user_exists && (
                <p className="text-sm text-brand-500">
                  Already have an account?{" "}
                  <Link to={loginHref} className="link-glow">
                    Sign in
                  </Link>
                </p>
              )}
            </div>
          )}
        </motion.div>
      ) : !preview ? (
        <div className="glass-panel flex items-start gap-3 p-6 text-brand-300">
          <AlertCircle size={20} className="mt-0.5 shrink-0 text-rose-400" />
          <div>
            <p className="font-medium text-brand-100">Invalid invitation link</p>
            <p className="mt-1 text-sm text-brand-400">
              This link is malformed or no longer exists. Request a new invitation from your
              administrator.
            </p>
          </div>
        </div>
      ) : null}
    </AuthLayout>
  );
}
