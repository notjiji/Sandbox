# Authentication (as built)

Implementation: `backend/app/auth/`, tokens in `refresh_tokens`. Settings in `app/core/config.py`.

## Mechanisms

| Mechanism | Behavior |
|-----------|----------|
| Password | Stored hashed on `users.hashed_password` |
| Access token | JWT, `JWT_ALGORITHM=HS256`, default 900 seconds |
| Refresh token | Opaque, **hashed** at rest, default 30 days, rotatable |
| Email verify | Hashed OTP, default 15 minutes, max 5 attempts |
| Password reset | Hashed token, default 1 hour |
| Lockout | `ACCOUNT_LOCKOUT_MAX_ATTEMPTS=5`, window 900s, duration 900s |
| Session | `X-Session-ID`; revoke one / others / all |
| Rate limit | `RATE_LIMIT_AUTH` default 10/minute on auth routes |

## Headers for API use after login

```
Authorization: Bearer <access_token>
X-Organization-ID: <uuid>   # required for org-scoped routes
X-Session-ID: <id>          # session binding when issued
```

## Production gates

When `ENVIRONMENT=production`:

- `SECRET_KEY` and `JWT_SECRET` must be ≥32 chars and not start with `change-me`
- `POSTGRES_PASSWORD` must not contain `changeme`
- `RESEND_API_KEY` is required (transactional email)

OpenAPI docs URLs are disabled.

## Not implemented

- OAuth/OIDC social login
- WebAuthn
- API keys as a product (audit names reserved only)
- MFA beyond email OTP verification
