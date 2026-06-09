# Production SOP - Background Remover SaaS

This document is an operations runbook for production deployment, maintenance, and API usage.
No credentials are included in this file by design.

---

## 1) Scope

- Deploy and run the Flask + MongoDB SaaS application.
- Operate user/admin access safely.
- Troubleshoot common incidents.
- Avoid insecure practices in production.

---

## 2) Key Features

- **Advanced Background Removal**: Powered by the state-of-the-art BiRefNet model for high-accuracy background extraction.
- **HD and Standard Modes**: Built-in resolution toggles to allow users to request either standard definition or high-definition processing.
- **Asynchronous Bulk Processing**:
  - Process multiple images simultaneously in a single batch.
  - Active progress monitoring and status tracking.
  - Results compiled and downloaded in a single ZIP archive.
  - Batch files automatically cleared from storage and memory after download or 1-hour expiration.
- **Developer-Friendly API**: Auto-generated personal API keys for each registered account, allowing direct API integration into scripts and workflow tools.
- **Configurable Daily Usage Quotas**: Automatic tracking of daily usage limits to control server resources.
- **Built-in Rate Limiting**: Request limits per minute per user to guarantee API stability.
- **Centralized Admin Control Panel**:
  - Detailed dashboard listing all registered users and roles.
  - Real-time statistics tracking for user activity (Today's usage, Total usage, and Remaining usage).
  - Ability to instantly block/unblock user access.
  - Complete exemption from daily limits, rate limits, file size limits, and bulk upload count limits for administrators.

---

## 3) Required Environment Variables

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

## 4) Deployment SOP (Terminal)

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

## 5) Runtime SOP

### 5.1 Daily startup

1. Ensure database connectivity is available.
2. Start application process.
3. Verify authentication route (`/login`) is reachable.
4. Verify admin dashboard (`/admin`) for admin users.
5. Perform one end-to-end background removal request.

### 5.2 User onboarding

1. User signs up through `/signup` (or provisioned by admin process).
2. Verify user appears in admin dashboard.
3. Confirm status is active and usage counters initialize correctly.

### 5.3 Block / unblock operations

1. Open `/admin`.
2. Locate user record.
3. Apply `Block` or `Unblock`.
4. Re-verify login/API access behavior.

### 5.4 Incident response

1. Inspect app logs/terminal output.
2. Verify `MONGO_URI` connectivity and network allowlist.
3. Validate user account status and remaining usage.
4. Check API rate-limit and threshold configuration.
5. Retry with valid image input and authenticated session.

---

## 6) API Reference & Operations

All API endpoints require either an active browser session cookie (for frontend clients) or a valid API key passed via the `x-api-key` request header.

### 6.1 Overview of API Authentication
- **Session Authentication**: Automatic when accessed via browser after logging in.
- **Header Authentication**: Add `x-api-key: <YOUR_API_KEY>` to the request headers.

---

### 6.2 Endpoint Details

#### 1. Get User Profile (`GET /me`)
Retrieves the profile and usage metadata of the authenticated user.
- **Request Type**: `GET`
- **Authentication**: Required (Session cookie or `x-api-key` header)
- **Response Format**: `application/json`
- **Response Fields**:
  - `username` (string): The registered username.
  - `api_key` (string): The unique user API key.
  - `today_usage` (int): Count of processing calls used today (returns `—` or `0` for administrators).
  - `total_usage` (int): Total lifetime processing calls (returns `—` or `0` for administrators).
  - `remaining_usage` (int/string): Remaining daily allowance (returns `"Unlimited"` for administrators).
  - `role` (string): User privilege level (`"user"` or `"admin"`).
  - `is_blocked` (bool): Flag indicating if the account has been disabled.
- **HTTP Status Codes**:
  - `200 OK`: Successful retrieval.
  - `401 Unauthorized`: No valid session or API key provided.

#### 2. Single Image Background Removal (`POST /api/v1/remove-bg`)
Removes the background from a single image and returns the transparent PNG.
- **Request Type**: `POST`
- **Content-Type**: `multipart/form-data`
- **Authentication**: Required (Session cookie or `x-api-key` header)
- **Parameters**:
  - `image` (file, required): Target image file. Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`. Maximum size: 10MB for regular users, unlimited for admins.
  - `resolution` (string, optional): Target output quality. Allowed values: `hd` or `standard`. Defaults to `hd`.
- **Response Format**: `image/png` (binary stream)
- **Response Headers**:
  - `X-Usage-Used` (string): Current day's usage count.
  - `X-Usage-Limit` (string): Daily allowance threshold (or `"Unlimited"` for administrators).
  - `X-Remaining-Usage` (string): Remaining allowance (or `"Unlimited"` for administrators).
- **HTTP Status Codes**:
  - `200 OK`: Success. Transparent PNG stream returned.
  - `400 Bad Request`: Missing file, empty filename, unsupported format, or oversized file.
  - `401 Unauthorized`: Invalid API key or unauthenticated session.
  - `403 Forbidden`: Account is blocked.
  - `429 Too Many Requests`: User daily quota exceeded, or per-minute rate-limit hit.
  - `500 Internal Server Error`: Background removal engine failed to process the image.

#### 3. Initiate Bulk Image Processing (`POST /api/v1/remove-bg/bulk`)
Submits multiple images for asynchronous batch processing.
- **Request Type**: `POST`
- **Content-Type**: `multipart/form-data`
- **Authentication**: Required (Session cookie or `x-api-key` header)
- **Parameters**:
  - `images` (files, required): Multiple image files uploaded under the same key. Regular users are limited to 20 files per batch; admins are exempt from this limit.
  - `resolution` (string, optional): Resolution level (`hd` or `standard`). Defaults to `hd`.
- **Response Format**: `application/json`
- **Response Fields**:
  - `batch_id` (string): The uniquely generated batch identifier.
  - `total` (int): Total number of files successfully accepted.
- **HTTP Status Codes**:
  - `200 OK`: Batch created and processing thread initialized.
  - `400 Bad Request`: No files provided, batch size limit exceeded, unsupported format, or file size limit exceeded.
  - `401 Unauthorized`: Unauthenticated session or invalid API key.
  - `429 Too Many Requests`: Usage limit or rate limit exceeded.

#### 4. Check Bulk Batch Status (`GET /api/v1/remove-bg/bulk/<batch_id>/status`)
Fetches the status and progress counter of a running bulk job.
- **Request Type**: `GET`
- **Authentication**: Required (Session cookie or `x-api-key` header; usage limits are not checked or decremented for status polling)
- **Response Format**: `application/json`
- **Response Fields**:
  - `status` (string): Batch status (`"processing"` or `"completed"`).
  - `total` (int): Total files in the batch.
  - `completed` (int): Successfully processed images.
  - `failed` (int): Processing failures.
  - `pending` (int): Images still in queue.
- **HTTP Status Codes**:
  - `200 OK`: Success.
  - `401 Unauthorized`: Unauthenticated.
  - `404 Not Found`: Batch ID not found or expired.

#### 5. Download Bulk Batch Results (`GET /api/v1/remove-bg/bulk/<batch_id>/download`)
Downloads a ZIP archive containing all successfully processed images for the batch. Cleans up the files and batch tracking context from the system upon completion.
- **Request Type**: `GET`
- **Authentication**: Required (Session cookie or `x-api-key` header)
- **Response Format**: `application/zip` (binary stream)
- **HTTP Status Codes**:
  - `200 OK`: Success. ZIP archive containing PNGs.
  - `400 Bad Request`: Batch processing is still in progress and not ready for download.
  - `401 Unauthorized`: Unauthenticated.
  - `404 Not Found`: Batch ID not found, already downloaded, or expired.

---

### 6.3 Administrative Endpoints

These endpoints are strictly restricted to accounts with the `"admin"` role.

#### 1. Get Admin Dashboard (`GET /admin`)
Renders the HTML administrative dashboard, displaying the system user list, roles, usage stats, and account status.
- **Request Type**: `GET`
- **Authentication**: Required (Admin session cookie required)
- **Response Format**: `text/html`
- **HTTP Status Codes**:
  - `200 OK`: Success.
  - `401 Unauthorized`: Unauthenticated session.
  - `403 Forbidden`: Authenticated user does not have `"admin"` role.

#### 2. Toggle User Block Status (`POST /admin/toggle-block/<username>`)
Enables or disables access for a specified user account.
- **Request Type**: `POST`
- **Authentication**: Required (Admin session cookie required)
- **Redirects**: Redirects back to `/admin` dashboard.
- **HTTP Status Codes**:
  - `302 Found`: Redirects to `/admin` dashboard after toggling block status.
  - `401 Unauthorized`: Unauthenticated session.
  - `403 Forbidden`: Authenticated user does not have `"admin"` role.
- **Constraints**: Only accounts with `"user"` role can be blocked. Attempts to block accounts with `"admin"` role are ignored to prevent locking out administrators.

---

## 7) Security SOP

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

## 8) Production Readiness Checklist

- [ ] `SECRET_KEY` set and non-default
- [ ] `MONGO_URI` set via environment
- [ ] DB network/IP allowlist configured
- [ ] HTTPS enabled at ingress/reverse proxy
- [ ] `SESSION_COOKIE_SECURE=true`
- [ ] Admin bootstrap credentials not stored in repo
- [ ] Smoke test passed (`/login`, `/admin`, `/api/v1/remove-bg`)
- [ ] Operational owner assigned for monitoring and incident response

---

## 9) Troubleshooting Quick Guide

- App fails at startup with config error:
  - Required env vars are missing (`SECRET_KEY`, `MONGO_URI`).
- Login works but admin panel denied:
  - Logged-in user is not admin role.
- API returns `429`:
  - User hit daily limit or per-minute rate limit.
- API returns `500`:
  - Check image validity, model/runtime dependencies, and logs.

---

## 10) Change Control SOP

Before release:

1. Run dependency install in clean environment.
2. Run syntax/lint checks.
3. Validate critical routes and one full upload flow.
4. Review config changes for secret exposure.
5. Approve and deploy through standard release process.

