# Authentication

Sandbox uses JWT access tokens with refresh tokens and server-side session tracking. Email verification is required before full access.

## Endpoints

Base: `/api/v1/auth`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/register` | Create account (optional invite token) |
| POST | `/verify-email` | Confirm email with OTP |
| POST | `/resend-verification` | Resend OTP |
| POST | `/login` | Issue access + refresh tokens |
| POST | `/refresh` | Rotate access token |
| POST | `/logout` | Revoke session |
| POST | `/forgot-password` | Request reset email |
| POST | `/reset-password` | Set new password with token |
| POST | `/change-password` | Change password (authenticated) |

Rate limited via `RATE_LIMIT_AUTH` (default `10/minute` on auth routes).

## Session model

- Access token: short-lived JWT (default 15 minutes)
- Refresh token: longer-lived, stored hashed server-side
- `X-Session-ID` header ties requests to a revocable session
- Account lockout after repeated failed logins (`ACCOUNT_LOCKOUT_*` settings)

## Organization context

Auth endpoints are user-scoped. After login, the client selects an organization and sends:

```
Authorization: Bearer <access_token>
X-Organization-ID: <org_uuid>
```

Org-scoped routes reject requests missing the organization header.

## Security features

| Feature | Config / location |
|---------|-------------------|
| Password hashing | Argon2 + bcrypt fallback (`core/security.py`) |
| JWT signing | `JWT_SECRET`, `JWT_ALGORITHM` |
| Email OTP | `EMAIL_VERIFICATION_OTP_*` settings |
| Lockout | `ACCOUNT_LOCKOUT_*` settings |
| Password reset expiry | `PASSWORD_RESET_TOKEN_EXPIRE_HOURS` |

## Key files

| Area | Path |
|------|------|
| Router | `backend/app/auth/router.py` |
| Auth service | `backend/app/auth/services/auth_service.py` |
| Sessions | `backend/app/auth/services/session_service.py` |
| Lockout | `backend/app/auth/lockout.py` |
| Frontend | `frontend/src/features/auth/` |

## Diagrams

See [../diagrams/](../diagrams/):

- `register flow.png`
- `login flow.png`
- `token lifecycle.png`
- `auto-refresh.png`

## Token lifecycle detail

[token-lifecycle.md](./token-lifecycle.md)

## Audit events

Login, logout, failed login, lockout, password changes, and email verification are recorded. See [../audit/event-catalog.md](../audit/event-catalog.md).
