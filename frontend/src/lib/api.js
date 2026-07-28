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
  const { method = "GET", body, headers = {} } = options;
  const requestId = createRequestId();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": requestId,
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = payload?.error ?? {};
    throw new ApiError(
      error.code ?? "HTTP_ERROR",
      error.message ?? "Request failed",
      response.status,
      error.details ?? null,
    );
  }

  return payload;
}

export const authApi = {
  login: (data) => apiRequest("/auth/login", { method: "POST", body: data }),
  register: (data) => apiRequest("/auth/register", { method: "POST", body: data }),
  forgotPassword: (data) =>
    apiRequest("/auth/forgot-password", { method: "POST", body: data }),
};
