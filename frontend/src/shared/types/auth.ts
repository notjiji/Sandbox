export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  session_id?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  invite_token?: string;
}

export interface VerifyEmailRequest {
  email: string;
  otp: string;
}

export interface ResendVerificationRequest {
  email: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface SessionSummary {
  id: string;
  created_at: string;
  expires_at: string;
  is_current: boolean;
}

export interface SessionListResponse {
  items: SessionSummary[];
  total: number;
}

export interface RevokeSessionResponse {
  message: string;
  revoked_current_session?: boolean;
}

export interface MessageResponse {
  message: string;
}

export interface RegisterOrganizationSummary {
  id: string;
  name: string;
  slug: string;
  role: string;
}

export interface RegisterResponse extends MessageResponse {
  email: string;
  organization?: RegisterOrganizationSummary | null;
}
