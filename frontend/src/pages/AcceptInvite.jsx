import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle2, LogIn, UserPlus } from "lucide-react";
import AuthLayout from "../components/AuthLayout";
import FormAlert from "../components/FormAlert";
import { authApi, orgApi, ApiError, unwrapData } from "../lib/api";
import { tokenStorage } from "../lib/auth";
import { orgStorage } from "../lib/org";

export default function AcceptInvite() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [preview, setPreview] = useState(null);
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
        const data = unwrapData(await orgApi.previewInvite(token));
        if (active) setPreview(data);
      } catch (error) {
        if (active) {
          setAlert(error instanceof ApiError ? error.message : "Invalid invitation.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadPreview();
    return () => {
      active = false;
    };
  }, [token]);

  const handleAccept = async () => {
    if (!token) return;
    setAccepting(true);
    setAlert("");
    try {
      const organization = unwrapData(await orgApi.acceptInviteToken(token));
      orgStorage.setActiveOrgId(organization.id);
      navigate("/dashboard");
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
      ) : preview ? (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel space-y-6 p-8"
        >
          <div>
            <p className="terminal-text text-brand-500">{">"} invite.sys</p>
            <h2 className="mt-2 text-2xl font-bold text-brand-100">{preview.organization_name}</h2>
            <p className="mt-2 text-brand-400">
              {preview.inviter_name} invited <strong>{preview.email}</strong> as{" "}
              <strong>{preview.role}</strong>.
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
              {accepting ? "Accepting..." : "Accept invitation"}
            </button>
          ) : (
            <div className="space-y-3">
              {preview.user_exists ? (
                <Link to={loginHref} className="btn-primary inline-flex w-full items-center justify-center gap-2">
                  <LogIn size={18} />
                  Sign in to accept
                </Link>
              ) : (
                <Link to={registerHref} className="btn-primary inline-flex w-full items-center justify-center gap-2">
                  <UserPlus size={18} />
                  Create account to join
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
      ) : null}
    </AuthLayout>
  );
}
