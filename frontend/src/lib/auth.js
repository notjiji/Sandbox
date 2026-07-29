const ACCESS_TOKEN_KEY = "sandbox_access_token";
const REFRESH_TOKEN_KEY = "sandbox_refresh_token";
const TOKEN_EXPIRY_KEY = "sandbox_token_expiry";

export const tokenStorage = {
  setTokens({ access_token, refresh_token, expires_in }) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
    localStorage.setItem(
      TOKEN_EXPIRY_KEY,
      String(Date.now() + expires_in * 1000),
    );
  },

  getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  clear() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  },
};
