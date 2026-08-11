# Token Lifecycle

## Tokens

| Token | Lifetime | Storage | Purpose |
|-------|----------|---------|---------|
| Access token | ~15 min (`JWT_ACCESS_TOKEN_EXPIRE_SECONDS`) | Client memory / `tokenStorage` | API authorization |
| Refresh token | ~30 days (`JWT_REFRESH_TOKEN_EXPIRE_DAYS`) | HttpOnly cookie + client storage | Obtain new access token |
| Session ID | Session lifetime | Header `X-Session-ID` | Revocation, device tracking |

## Login flow

```
POST /auth/login
    → verify password (+ lockout check)
    → create Session row
    → return { access_token, refresh_token, session_id, user }
```

Frontend stores tokens via `frontend/src/features/auth/storage.ts` and attaches them in `shared/api/client.ts`.

## Refresh flow

```
POST /auth/refresh  { refresh_token }
    → validate hashed refresh token in DB
    → issue new access_token (and optionally rotate refresh)
    → return { access_token, … }
```

The API client automatically refreshes on 401 when a refresh token is available.

## Logout

```
POST /auth/logout
    → invalidate session
    → clear refresh token association
```

## JWT payload (access token)

Contains at minimum:

- `sub` — user ID
- `email`
- `type` — `"access"`
- Optional org/role claims may be embedded for the active org context

Verify with `JWT_SECRET` and `JWT_ALGORITHM` (default HS256).

## Invite-on-register

Registration accepts an optional `invite_token`. When present, the user is linked to the inviting organization upon verification instead of creating a standalone account flow.

## Frontend auto-refresh

See diagram: [../diagrams/auto-refresh.png](../diagrams/auto-refresh.png)

Implementation: `refreshAccessToken()` in `frontend/src/shared/api/client.ts` — called transparently by `apiRequest` and binary fetch helpers on 401.

## Security notes

- Never commit real `JWT_SECRET` or `SECRET_KEY` values
- Production requires secrets ≥ 32 characters (validated in `Settings`)
- Refresh tokens are stored hashed server-side, not in plaintext
