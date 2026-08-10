import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "@/features/auth/components/ProtectedRoute";
import OrgProtectedRoute from "@/features/organizations/components/OrgProtectedRoute";
import Landing from "@/shared/pages/Landing";
import NotFound from "@/shared/pages/NotFound";
import Login from "@/features/auth/pages/Login";
import Register from "@/features/auth/pages/Register";
import ForgotPassword from "@/features/auth/pages/ForgotPassword";
import ResetPassword from "@/features/auth/pages/ResetPassword";
import VerifyEmail from "@/features/auth/pages/VerifyEmail";
import Settings from "@/features/auth/pages/Settings";
import Profile from "@/features/users/pages/Profile";
import AcceptInvite from "@/features/members/pages/AcceptInvite";
import SelectOrganization from "@/features/organizations/pages/SelectOrganization";
import Welcome from "@/features/organizations/pages/Welcome";
import Dashboard from "@/features/organizations/pages/Dashboard";
import OrgSettings from "@/features/organizations/pages/OrgSettings";
import OrganizationActivity from "@/features/organizations/pages/Activity";
import Members from "@/features/members/pages/Members";
import Projects from "@/features/projects/pages/Projects";
import ProjectDetail from "@/features/projects/pages/ProjectDetail";
import ProjectSettings from "@/features/projects/pages/ProjectSettings";
import Assets from "@/features/assets/pages/Assets";
import AssetDetail from "@/features/assets/pages/AssetDetail";
import AssetEdit from "@/features/assets/pages/AssetEdit";
import AssetNew from "@/features/assets/pages/AssetNew";
import Scans from "@/features/scans/pages/Scans";
import Findings from "@/features/findings/pages/Findings";
import AssetFindings from "@/features/findings/pages/AssetFindings";
import Reports from "@/features/reports/pages/Reports";
import OrgReports from "@/features/reports/pages/OrgReports";
import AssetReports from "@/features/reports/pages/AssetReports";
import AiAssistant from "@/features/ai/pages/AiAssistant";

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
        <Route path="/welcome" element={<Welcome />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />

        <Route element={<OrgProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/organization/settings" element={<OrgSettings />} />
          <Route path="/organization/activity" element={<OrganizationActivity />} />
          <Route path="/organization/members" element={<Members />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:projectId" element={<ProjectDetail />} />
          <Route path="/projects/:projectId/settings" element={<ProjectSettings />} />
          <Route path="/projects/:projectId/assets" element={<Assets />} />
          <Route path="/projects/:projectId/assets/new" element={<AssetNew />} />
          <Route path="/projects/:projectId/assets/:assetId/edit" element={<AssetEdit />} />
          <Route path="/projects/:projectId/assets/:assetId" element={<AssetDetail />} />
          <Route path="/projects/:projectId/assets/:assetId/scans" element={<Scans />} />
          <Route path="/projects/:projectId/assets/:assetId/findings" element={<AssetFindings />} />
          <Route path="/projects/:projectId/assets/:assetId/reports" element={<AssetReports />} />
          <Route path="/reports" element={<OrgReports />} />
          <Route path="/projects/:projectId/findings" element={<Findings />} />
          <Route path="/projects/:projectId/reports" element={<Reports />} />
          <Route path="/ai-assistant" element={<AiAssistant />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
