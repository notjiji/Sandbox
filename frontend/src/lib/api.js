import { tokenStorage } from "./auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

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

export async function apiRequest(path, options = {}) {
  const { method = "GET", body, headers = {}, auth = false } = options;
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
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    credentials: "include",
    headers: requestHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = payload?.error ?? {};
    throw new ApiError(
      error.code ?? "HTTP_ERROR",
      error.message ?? payload?.message ?? "Request failed",
      response.status,
      error.details ?? null,
    );
  }

  return payload;
}

export const authApi = {
  register: (data) => apiRequest("/auth/register", { method: "POST", body: data }),
  login: async (data) => {
    const payload = await apiRequest("/auth/login", { method: "POST", body: data });
    tokenStorage.setTokens(payload);
    return payload;
  },
  refresh: async (refreshToken) => {
    const payload = await apiRequest("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken ?? tokenStorage.getRefreshToken() },
    });
    tokenStorage.setTokens(payload);
    return payload;
  },
  logout: async () => {
    const refreshToken = tokenStorage.getRefreshToken();
    if (refreshToken) {
      await apiRequest("/auth/logout", {
        method: "POST",
        body: { refresh_token: refreshToken },
      });
    }
    tokenStorage.clear();
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
};
