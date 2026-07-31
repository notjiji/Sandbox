import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "../components/ProtectedRoute";
import OrgProtectedRoute from "../components/OrgProtectedRoute";
import Landing from "../pages/Landing";
import Login from "../pages/Login";
import Register from "../pages/Register";
import ForgotPassword from "../pages/ForgotPassword";
import ResetPassword from "../pages/ResetPassword";
import VerifyEmail from "../pages/VerifyEmail";
import AcceptInvite from "../pages/AcceptInvite";
import SelectOrganization from "../pages/SelectOrganization";
import Dashboard from "../pages/Dashboard";
import OrgSettings from "../pages/OrgSettings";
import Members from "../pages/Members";
import Projects from "../pages/Projects";
import Profile from "../pages/Profile";
import Settings from "../pages/Settings";
import NotFound from "../pages/NotFound";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/accept-invite" element={<AcceptInvite />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/select-organization" element={<SelectOrganization />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />

        <Route element={<OrgProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/organization/settings" element={<OrgSettings />} />
          <Route path="/organization/members" element={<Members />} />
          <Route path="/projects" element={<Projects />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
