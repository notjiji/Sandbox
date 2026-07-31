import { notifySessionExpired, tokenStorage } from "./auth";
import { orgStorage } from "./org";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

/** Auth routes that must never trigger the refresh interceptor. */
const AUTH_PATHS_NO_REFRESH = new Set([
  "/auth/login",
  "/auth/register",
  "/auth/refresh",
  "/auth/logout",
  "/auth/forgot-password",
  "/auth/reset-password",
  "/auth/verify-email",
  "/auth/resend-verification",
]);

let refreshPromise = null;

function createRequestId() {
  return crypto.randomUUID();
}

export class ApiError extends Error {
  constructor(code, message, status, details = null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

function parseErrorPayload(payload, response) {
  const error = payload?.error ?? {};
  return new ApiError(
    error.code ?? "HTTP_ERROR",
    error.message ?? payload?.message ?? "Request failed",
    response.status,
    error.details ?? null,
  );
}

async function rawApiRequest(path, options = {}) {
  const { method = "GET", body, headers = {}, auth = false, organizationId = undefined } = options;
  const requestId = createRequestId();
  const requestHeaders = {
    "Content-Type": "application/json",
    "X-Request-ID": requestId,
    ...headers,
  };

  if (auth) {
    const accessToken = tokenStorage.getAccessToken();
    if (accessToken) {
      requestHeaders.Authorization = `Bearer ${accessToken}`;
    }
    const sessionId = tokenStorage.getSessionId();
    if (sessionId) {
      requestHeaders["X-Session-ID"] = sessionId;
    }
    const resolvedOrgId =
      organizationId !== undefined ? organizationId : orgStorage.getActiveOrgId();
    if (resolvedOrgId) {
      requestHeaders["X-Organization-ID"] = resolvedOrgId;
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    credentials: "include",
    headers: requestHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw parseErrorPayload(payload, response);
  }

  return payload;
}

async function performTokenRefresh() {
  const refreshToken = tokenStorage.getRefreshToken();
  if (!refreshToken) {
    throw new ApiError("UNAUTHORIZED", "No refresh token available", 401);
  }

  const payload = await rawApiRequest("/auth/refresh", {
    method: "POST",
    body: { refresh_token: refreshToken },
  });

  tokenStorage.setTokens(payload);
  return payload;
}

export async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = performTokenRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function ensureFreshAccessToken() {
  if (!tokenStorage.isAuthenticated()) return;
  if (tokenStorage.shouldRefreshAccessToken()) {
    await refreshAccessToken();
  }
}

function redirectToLogin() {
  const { pathname, search } = window.location;
  if (pathname === "/login" || pathname === "/register") return;

  const params = new URLSearchParams(search);
  params.set("reason", "session-expired");
  const returnTo = pathname !== "/" ? pathname : "";
  if (returnTo) {
    params.set("from", returnTo);
  }

  const query = params.toString();
  window.location.replace(`/login${query ? `?${query}` : ""}`);
}

function handleSessionExpired() {
  notifySessionExpired();
  redirectToLogin();
}

function shouldAttemptRefresh(path, options, retried) {
  return (
    options.auth &&
    !retried &&
    !AUTH_PATHS_NO_REFRESH.has(path) &&
    Boolean(tokenStorage.getRefreshToken())
  );
}

export async function apiRequest(path, options = {}, retried = false) {
  if (options.auth && !retried) {
    try {
      await ensureFreshAccessToken();
    } catch {
      handleSessionExpired();
      throw new ApiError("UNAUTHORIZED", "Session expired", 401);
    }
  }

  try {
    return await rawApiRequest(path, options);
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.status === 401 &&
      shouldAttemptRefresh(path, options, retried)
    ) {
      try {
        await refreshAccessToken();
        return apiRequest(path, options, true);
      } catch {
        handleSessionExpired();
        throw new ApiError("UNAUTHORIZED", "Session expired", 401);
      }
    }
    throw error;
  }
}

function unwrapData(payload) {
  return payload?.data ?? payload;
}

export const authApi = {
  register: (data) => apiRequest("/auth/register", { method: "POST", body: data }),
  verifyEmail: (data) =>
    apiRequest("/auth/verify-email", { method: "POST", body: data }),
  resendVerification: (data) =>
    apiRequest("/auth/resend-verification", { method: "POST", body: data }),
  login: async (data) => {
    const payload = await apiRequest("/auth/login", { method: "POST", body: data });
    tokenStorage.setTokens(payload);
    return payload;
  },
  refresh: () => refreshAccessToken(),
  logout: async () => {
    const refreshToken = tokenStorage.getRefreshToken();
    if (refreshToken) {
      try {
        await rawApiRequest("/auth/logout", {
          method: "POST",
          body: { refresh_token: refreshToken },
        });
      } catch {
        // Clear local session even if revoke fails (expired token, offline, etc.)
      }
    }
    tokenStorage.clear();
    orgStorage.clear();
  },
  forgotPassword: (data) =>
    apiRequest("/auth/forgot-password", {
      method: "POST",
      body: { email: data.email.trim().toLowerCase() },
    }),
  resetPassword: (data) =>
    apiRequest("/auth/reset-password", { method: "POST", body: data }),
  changePassword: (data) =>
    apiRequest("/auth/change-password", { method: "PUT", body: data, auth: true }),
  getMe: () => apiRequest("/users/me", { auth: true }),
  updateMe: (data) =>
    apiRequest("/users/me", { method: "PATCH", body: data, auth: true }),
  listSessions: () => apiRequest("/auth/sessions", { auth: true }),
  revokeSession: (sessionId) =>
    apiRequest(`/auth/sessions/${sessionId}`, { method: "DELETE", auth: true }),
  revokeOtherSessions: () =>
    apiRequest("/auth/sessions/revoke-others", { method: "POST", auth: true }),
  revokeAllSessions: () =>
    apiRequest("/auth/sessions/revoke-all", { method: "POST", auth: true }),
};

export const orgApi = {
  listMine: () => apiRequest("/organizations/me", { auth: true }),
  create: (data) =>
    apiRequest("/organizations", { method: "POST", body: data, auth: true }),
  getCurrent: () => apiRequest("/organizations/current", { auth: true }),
  updateCurrent: (data) =>
    apiRequest("/organizations/current", { method: "PATCH", body: data, auth: true }),
  deleteCurrent: () =>
    apiRequest("/organizations/current", { method: "DELETE", auth: true }),
  listMembers: () => apiRequest("/organizations/current/members", { auth: true }),
  listInvites: () => apiRequest("/organizations/current/invites", { auth: true }),
  inviteMember: (data) =>
    apiRequest("/organizations/current/members", {
      method: "POST",
      body: data,
      auth: true,
    }),
  acceptInvitation: (organizationId) =>
    apiRequest("/organizations/current/members/accept", {
      method: "POST",
      auth: true,
      organizationId,
    }),
  updateMember: (membershipId, data) =>
    apiRequest(`/organizations/current/members/${membershipId}`, {
      method: "PATCH",
      body: data,
      auth: true,
    }),
  removeMember: (membershipId) =>
    apiRequest(`/organizations/current/members/${membershipId}`, {
      method: "DELETE",
      auth: true,
    }),
  revokeInvite: (inviteId) =>
    apiRequest(`/organizations/current/invites/${inviteId}`, {
      method: "DELETE",
      auth: true,
    }),
  previewInvite: (token) => apiRequest(`/organizations/invites/${token}`),
  acceptInviteToken: (token) =>
    apiRequest(`/organizations/invites/${token}/accept`, {
      method: "POST",
      auth: true,
      organizationId: null,
    }),
  listRoles: () => apiRequest("/organizations/roles"),
};

export const projectApi = {
  list: () => apiRequest("/projects", { auth: true }),
  create: (data) => apiRequest("/projects", { method: "POST", body: data, auth: true }),
  get: (projectId) => apiRequest(`/projects/${projectId}`, { auth: true }),
  update: (projectId, data) =>
    apiRequest(`/projects/${projectId}`, { method: "PATCH", body: data, auth: true }),
  delete: (projectId) =>
    apiRequest(`/projects/${projectId}`, { method: "DELETE", auth: true }),
};

export { unwrapData };
