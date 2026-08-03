import { orgStorage } from "@/features/organizations/storage";
import type { AuthTokens } from "@/shared/types/auth";

const ACCESS_TOKEN_KEY = "sandbox_access_token";
const REFRESH_TOKEN_KEY = "sandbox_refresh_token";
const TOKEN_EXPIRY_KEY = "sandbox_token_expiry";
const SESSION_ID_KEY = "sandbox_session_id";

/** Refresh access token this many ms before JWT expiry. */
export const TOKEN_REFRESH_BUFFER_MS = 60_000;

export const tokenStorage = {
  setTokens({ access_token, refresh_token, expires_in, session_id }: AuthTokens): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
    localStorage.setItem(TOKEN_EXPIRY_KEY, String(Date.now() + expires_in * 1000));
    if (session_id) {
      localStorage.setItem(SESSION_ID_KEY, session_id);
    }
  },

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  getSessionId(): string | null {
    return localStorage.getItem(SESSION_ID_KEY);
  },

  getTokenExpiry(): number | null {
    const raw = localStorage.getItem(TOKEN_EXPIRY_KEY);
    return raw ? Number(raw) : null;
  },

  isAuthenticated(): boolean {
    return Boolean(this.getAccessToken() && this.getRefreshToken());
  },

  shouldRefreshAccessToken(bufferMs = TOKEN_REFRESH_BUFFER_MS): boolean {
    const expiry = this.getTokenExpiry();
    if (!expiry) return true;
    return Date.now() >= expiry - bufferMs;
  },

  clear(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    localStorage.removeItem(SESSION_ID_KEY);
  },
};

export const AUTH_SESSION_EXPIRED_EVENT = "auth:session-expired";

export function notifySessionExpired(): void {
  tokenStorage.clear();
  orgStorage.clear();
  window.dispatchEvent(new CustomEvent(AUTH_SESSION_EXPIRED_EVENT));
}
