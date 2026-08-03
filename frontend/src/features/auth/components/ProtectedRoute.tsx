import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { AUTH_SESSION_EXPIRED_EVENT, tokenStorage } from "../storage";

interface AuthLocationState {
  from?: string;
}

export default function ProtectedRoute() {
  const location = useLocation();
  const authState = location.state as AuthLocationState | null;
  const [allowed, setAllowed] = useState(() => tokenStorage.isAuthenticated());

  useEffect(() => {
    const syncAuth = () => setAllowed(tokenStorage.isAuthenticated());
    window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, syncAuth);
    return () => window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, syncAuth);
  }, []);

  if (!allowed) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet context={authState} />;
}
