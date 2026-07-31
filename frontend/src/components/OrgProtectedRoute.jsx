import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { orgApi } from "../lib/api";
import { tokenStorage } from "../lib/auth";
import {
  getActiveOrganizations,
  orgStorage,
  resolveActiveOrganization,
} from "../lib/org";

export default function OrgProtectedRoute() {
  const location = useLocation();
  const [state, setState] = useState({ loading: true, allowed: false, reason: "auth" });

  useEffect(() => {
    let active = true;

    async function verifyAccess() {
      if (!tokenStorage.isAuthenticated()) {
        if (active) setState({ loading: false, allowed: false, reason: "auth" });
        return;
      }

      try {
        const payload = await orgApi.listMine();
        if (!active) return;

        const activeOrgId = resolveActiveOrganization(payload);

        if (!activeOrgId) {
          setState({ loading: false, allowed: false, reason: "select-org" });
          return;
        }

        const activeOrgs = getActiveOrganizations(payload);
        if (!activeOrgs.some((org) => org.id === activeOrgId)) {
          orgStorage.clear();
          setState({ loading: false, allowed: false, reason: "select-org" });
          return;
        }

        setState({ loading: false, allowed: true, reason: null });
      } catch {
        if (active) setState({ loading: false, allowed: false, reason: "select-org" });
      }
    }

    verifyAccess();
    return () => {
      active = false;
    };
  }, [location.pathname]);

  if (state.loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-void text-brand-400">
        Loading workspace...
      </div>
    );
  }

  if (!state.allowed) {
    if (state.reason === "auth") {
      return <Navigate to="/login" replace state={{ from: location.pathname }} />;
    }
    return <Navigate to="/select-organization" replace />;
  }

  return <Outlet />;
}
