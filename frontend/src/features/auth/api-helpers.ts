import type { ApiRequestOptions } from "@/shared/types/api";
import { unwrapData } from "@/shared/api/client";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

/** Low-level fetch for auth logout (no refresh interceptor). */
export async function rawApiRequest<T = unknown>(
  path: string,
  options: Pick<ApiRequestOptions, "method" | "body" | "headers"> = {},
): Promise<T> {
  const { method = "GET", body, headers = {} } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const payload: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error =
      typeof payload === "object" &&
      payload !== null &&
      "error" in payload &&
      typeof (payload as { error?: { message?: string } }).error?.message === "string"
        ? (payload as { error: { message: string } }).error.message
        : "Request failed";
    throw new Error(error);
  }
  return unwrapData<T>(payload);
}
