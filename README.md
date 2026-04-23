# Production SOP - Background Remover SaaS

This document is an operations runbook for production deployment and maintenance.
No credentials are included in this file by design.

---

## 1) Scope

- Deploy and run the Flask + MongoDB SaaS application.
- Operate user/admin access safely.
- Troubleshoot common incidents.
- Avoid insecure practices in production.

---

## 2) Required Environment Variables

Set these before starting the app:

- `SECRET_KEY` (strong random value, required)
- `MONGO_URI` (required)
- `MONGO_DB_NAME` (recommended; default `bg_saas`)

Operational controls:

- `SESSION_COOKIE_SECURE` (set `true` in production)
- `DAILY_USAGE_LIMIT`
- `FAILED_ATTEMPTS_THRESHOLD`
- `RATE_LIMIT_PER_MINUTE`

Optional admin bootstrap:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

---

## 3) Deployment SOP (Terminal)

From project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py
```

Health checks:

- Open `/login` and confirm page loads.
- Authenticate with an authorized account.
- Access `/admin` using an admin-role account.
- Upload one test image in `/app` and verify output.

---

## 4) Runtime SOP

### 4.1 Daily startup

1. Ensure database connectivity is available.
2. Start application process.
3. Verify authentication route (`/login`) is reachable.
4. Verify admin dashboard (`/admin`) for admin users.
5. Perform one end-to-end background removal request.

### 4.2 User onboarding

1. User signs up through `/signup` (or provisioned by admin process).
2. Verify user appears in admin dashboard.
3. Confirm status is active and usage counters initialize correctly.

### 4.3 Block / unblock operations

1. Open `/admin`.
2. Locate user record.
3. Apply `Block` or `Unblock`.
4. Re-verify login/API access behavior.

### 4.4 Incident response

1. Inspect app logs/terminal output.
2. Verify `MONGO_URI` connectivity and network allowlist.
3. Validate user account status and remaining usage.
4. Check API rate-limit and threshold configuration.
5. Retry with valid image input and authenticated session.

---

## 5) API Operations SOP

Endpoint:

- `POST /api/v1/remove-bg`

Request:

- `multipart/form-data`
- image field: `image`

Auth:

- Session user (browser flow), or API key header (`x-api-key`) for API clients.

Response:

- PNG output stream
- Usage headers:
  - `X-Usage-Used`
  - `X-Usage-Limit`
  - `X-Remaining-Usage`

Expected errors:

- `400` bad request / missing file
- `401` unauthenticated / invalid key
- `403` blocked account
- `429` limit exceeded
- `500` processing failure

---

## 6) Security SOP

Do this:

- Store all secrets in environment variables or secret manager.
- Enforce HTTPS in front of the app.
- Keep `SESSION_COOKIE_SECURE=true` in production.
- Rotate credentials and keys periodically.
- Restrict DB user permissions to least privilege.

Do NOT do this:

- Do not commit credentials, usernames, passwords, or connection strings to git.
- Do not hardcode secrets in code, templates, scripts, or docs.
- Do not disable auth/admin decorators.
- Do not grant admin role without explicit authorization.
- Do not bypass usage and rate-limit safeguards.

---

## 7) Production Readiness Checklist

- [ ] `SECRET_KEY` set and non-default
- [ ] `MONGO_URI` set via environment
- [ ] DB network/IP allowlist configured
- [ ] HTTPS enabled at ingress/reverse proxy
- [ ] `SESSION_COOKIE_SECURE=true`
- [ ] Admin bootstrap credentials not stored in repo
- [ ] Smoke test passed (`/login`, `/admin`, `/api/v1/remove-bg`)
- [ ] Operational owner assigned for monitoring and incident response

---

## 8) Troubleshooting Quick Guide

- App fails at startup with config error:
  - Required env vars are missing (`SECRET_KEY`, `MONGO_URI`).
- Login works but admin panel denied:
  - Logged-in user is not admin role.
- API returns `429`:
  - User hit daily limit or per-minute rate limit.
- API returns `500`:
  - Check image validity, model/runtime dependencies, and logs.

---

## 9) Change Control SOP

Before release:

1. Run dependency install in clean environment.
2. Run syntax/lint checks.
3. Validate critical routes and one full upload flow.
4. Review config changes for secret exposure.
5. Approve and deploy through standard release process.
