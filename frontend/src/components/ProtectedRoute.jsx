import { Navigate, Outlet, useLocation } from "react-router-dom";
import { tokenStorage } from "../lib/auth";

export default function ProtectedRoute() {
  const location = useLocation();
  const accessToken = tokenStorage.getAccessToken();

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
