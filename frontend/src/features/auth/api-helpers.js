const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

/** Low-level fetch for auth logout (no refresh interceptor). */
export async function rawApiRequest(path, options = {}) {
  const { method = "GET", body, headers = {} } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = payload?.error ?? {};
    throw new Error(error.message ?? "Request failed");
  }
  return payload;
}
