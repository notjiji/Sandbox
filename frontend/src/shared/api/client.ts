import { tokenStorage, notifySessionExpired } from "@/features/auth/storage";
import { orgStorage } from "@/features/organizations/storage";
import type { ApiEnvelope, ApiErrorBody, ApiRequestOptions } from "@/shared/types/api";
import type { AuthTokens } from "@/shared/types/auth";

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

let refreshPromise: Promise<AuthTokens> | null = null;

function createRequestId(): string {
  return crypto.randomUUID();
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: unknown;

  constructor(code: string, message: string, status: number, details: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function parseErrorPayload(payload: unknown, response: Response): ApiError {
  const body = isRecord(payload) ? payload : {};
  const error = isRecord(body.error) ? body.error : {};
  const message =
    typeof error.message === "string"
      ? error.message
      : typeof body.message === "string"
        ? body.message
        : "Request failed";

  return new ApiError(
    typeof error.code === "string" ? error.code : "HTTP_ERROR",
    message,
    response.status,
    error.details ?? null,
  );
}

async function rawApiRequest<T = unknown>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { method = "GET", body, headers = {}, auth = false, organizationId = undefined } =
    options;
  const requestId = createRequestId();
  const requestHeaders: Record<string, string> = {
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
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const payload: unknown = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw parseErrorPayload(payload, response);
  }

  return unwrapData<T>(payload);
}

async function performTokenRefresh(): Promise<AuthTokens> {
  const refreshToken = tokenStorage.getRefreshToken();
  if (!refreshToken) {
    throw new ApiError("UNAUTHORIZED", "No refresh token available", 401);
  }

  const payload = await rawApiRequest<AuthTokens>("/auth/refresh", {
    method: "POST",
    body: { refresh_token: refreshToken },
  });

  tokenStorage.setTokens(payload);
  return payload;
}

export async function refreshAccessToken(): Promise<AuthTokens> {
  if (!refreshPromise) {
    refreshPromise = performTokenRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function ensureFreshAccessToken(): Promise<void> {
  if (!tokenStorage.isAuthenticated()) return;
  if (tokenStorage.shouldRefreshAccessToken()) {
    await refreshAccessToken();
  }
}

function redirectToLogin(): void {
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

function handleSessionExpired(): void {
  notifySessionExpired();
  redirectToLogin();
}

function shouldAttemptRefresh(
  path: string,
  options: ApiRequestOptions,
  retried: boolean,
): boolean {
  return (
    Boolean(options.auth) &&
    !retried &&
    !AUTH_PATHS_NO_REFRESH.has(path) &&
    Boolean(tokenStorage.getRefreshToken())
  );
}

export async function apiRequest<T = unknown>(
  path: string,
  options: ApiRequestOptions = {},
  retried = false,
): Promise<T> {
  if (options.auth && !retried) {
    try {
      await ensureFreshAccessToken();
    } catch {
      handleSessionExpired();
      throw new ApiError("UNAUTHORIZED", "Session expired", 401);
    }
  }

  try {
    return await rawApiRequest<T>(path, options);
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.status === 401 &&
      shouldAttemptRefresh(path, options, retried)
    ) {
      try {
        await refreshAccessToken();
        return apiRequest<T>(path, options, true);
      } catch {
        handleSessionExpired();
        throw new ApiError("UNAUTHORIZED", "Session expired", 401);
      }
    }
    throw error;
  }
}

export function unwrapData<T>(payload: unknown): T {
  if (isRecord(payload) && payload.success === true && "data" in payload) {
    return (payload as unknown as ApiEnvelope<T>).data;
  }
  if (isRecord(payload) && "data" in payload && !("error" in payload)) {
    return (payload as unknown as ApiEnvelope<T>).data;
  }
  return payload as T;
}

export function isApiErrorBody(payload: unknown): payload is ApiErrorBody {
  return isRecord(payload) && payload.success === false && isRecord(payload.error);
}
