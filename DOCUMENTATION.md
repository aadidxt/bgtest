# Background Remover SaaS — API Documentation

## Overview

**Purpose**  
Web application that removes backgrounds from images using the [BiRefNet](https://huggingface.co/ZhengPeng7/BiRefNet) deep-learning model. Supports single-image processing and asynchronous bulk processing with real-time progress tracking.

**Base URL**  
`http://localhost:5001`  
API endpoints are prefixed with `/api/v1`.

**Authentication Methods**

| Method | Mechanism | Used By |
|---|---|---|
| Session cookie | `flask.session` (signed cookie, HttpOnly, SameSite=Lax) | Browser-based UI |
| API key | `X-API-Key` request header | Programmatic / API clients |

Session takes priority when both are present.

**Common Headers**

| Header | When | Value |
|---|---|---|
| `X-API-Key` | Programmatic requests | `bg_<32‑char‑urlsafe‑base64>` |
| `Content-Type` | File uploads | `multipart/form-data` |
| `Accept` | JSON responses | `application/json` |

**Rate Limits**  
- **30 requests per minute** per user (sliding 60-second window, in-memory).  
- **Admins are exempt** from rate limiting.

**Error Handling Conventions**  
All API errors return JSON:

```json
{
  "error": "Human-readable error description."
}
```

HTTP status codes indicate the error class (see [Response Status Codes](#response-status-codes)).

**User Roles**

| Role | Capabilities |
|---|---|
| `user` | Standard usage limits, rate-limited, file size/count capped |
| `admin` | Unlimited usage, no rate limits, no file caps, access to `/admin` |

---

## Authentication APIs

---

### `GET /signup`

Render the sign-up form.

- **Method:** `GET`
- **URL:** `/signup`
- **Authentication:** None
- **Response:** `200 OK` — HTML page (`signup.html`)

---

### `POST /signup`

Register a new user account.

- **Method:** `POST`
- **URL:** `/signup`
- **Authentication:** None

**Request Parameters**

| Field | Type | Required | Validation |
|---|---|---|---|
| `username` | `string` | Yes | 3–30 characters, regex `[A-Za-z0-9_]+` |
| `password` | `string` | Yes | Minimum 6 characters |

**Example Request**

```bash
curl -X POST http://localhost:5001/signup \
  -d "username=johndoe" \
  -d "password=secret123"
```

**Response**  
- **Success:** `302 Found` — redirects to `/app`; session cookie set.  
- **Failure:** `200 OK` — re-renders `signup.html` with a flash message.

**Error Responses**

| Status | Condition | Flash Message |
|---|---|---|
| 200 | Duplicate username | `"Username already exists."` |
| 200 | Invalid username | Validation error |
| 200 | Invalid password | Validation error |

---

### `GET /login`

Render the login form.

- **Method:** `GET`
- **URL:** `/login`
- **Authentication:** None
- **Response:** `200 OK` — HTML page (`login.html`)

---

### `POST /login`

Authenticate an existing user.

- **Method:** `POST`
- **URL:** `/login`
- **Authentication:** None

**Request Parameters**

| Field | Type | Required | Validation |
|---|---|---|---|
| `username` | `string` | Yes | Trimmed server-side |
| `password` | `string` | Yes | Bcrypt-verified against stored hash |

**Example Request**

```bash
curl -X POST http://localhost:5001/login \
  -d "username=johndoe" \
  -d "password=secret123"
```

**Response**

- **Success:** `302 Found` — redirects to `/app`; session cookie set; failed-attempts counter cleared.  
- **Failure:** `200 OK` — re-renders `login.html` with a flash message.

**Error Responses**

| Status | Condition | Flash Message |
|---|---|---|
| 200 | Wrong credentials | `"Invalid username or password."` |
| 200 | Account blocked | `"Your account is blocked."` |

---

### `GET /logout`

Clear the current session.

- **Method:** `GET`
- **URL:** `/logout`
- **Authentication:** None (session-checked)
- **Response:** `302 Found` — redirects to `/login`

---

### `GET /me`

Return the authenticated user's profile and usage information as JSON.

- **Method:** `GET`
- **URL:** `/me`
- **Authentication:** `@auth_required(api_mode=True, enforce_usage=False)` — session cookie **or** `X-API-Key` header

**Response:** `200 OK`

```json
{
  "username": "johndoe",
  "api_key": "bg_abc123...",
  "today_usage": 3,
  "total_usage": 27,
  "remaining_usage": 17,
  "role": "user",
  "is_blocked": false
}
```

**Response Fields**

| Field | Type | Description |
|---|---|---|
| `username` | `string` | Username |
| `api_key` | `string` | Auto-generated API key |
| `today_usage` | `integer` | API calls used today |
| `total_usage` | `integer` | Lifetime API calls |
| `remaining_usage` | `integer` | Calls remaining for today |
| `role` | `string` | `"user"` or `"admin"` |
| `is_blocked` | `boolean` | Whether the account is blocked |

**Error Responses**

| Status | Description |
|---|---|
| 401 | `{"error": "Authentication required"}` |
| 403 | `{"error": "User is blocked"}` |

---

## Background Removal APIs

---

### `POST /api/v1/remove-bg`

Remove the background from a single image.

- **Method:** `POST`
- **URL:** `/api/v1/remove-bg`
- **Authentication:** `@auth_required(api_mode=True, enforce_usage=True)` + `@rate_limit_per_user`
- **Required Headers:** `Content-Type: multipart/form-data`

**Request Parameters**

| Field | Type | Required | Default | Validation |
|---|---|---|---|---|
| `image` | `file` | Yes | — | Extension must be `.jpg`, `.jpeg`, `.png`, or `.webp`; max 10 MB (non-admin only) |
| `resolution` | `string` | No | `"hd"` | Must be `"hd"` or `"standard"`; invalid values fall back to `"hd"` |

**Example Request**

```bash
curl -X POST http://localhost:5001/api/v1/remove-bg \
  -H "X-API-Key: bg_abc123..." \
  -F "image=@photo.jpg" \
  -F "resolution=hd"
```

**Example Response**

- **Status:** `200 OK`
- **Content-Type:** `image/png`
- **Body:** Raw PNG image bytes (binary)

**Response Headers**

| Header | Non-Admin Value | Admin Value |
|---|---|---|
| `X-Usage-Used` | Integer (e.g. `"3"`) | `"0"` |
| `X-Usage-Limit` | Integer (e.g. `"20"`) | `"Unlimited"` |
| `X-Remaining-Usage` | Integer (e.g. `"17"`) | `"Unlimited"` |

**Error Responses**

| Status | Description |
|---|---|
| 400 | `{"error": "No image file provided."}` |
| 400 | `{"error": "Empty filename."}` |
| 401 | `{"error": "Authentication required"}` |
| 403 | `{"error": "User is blocked"}` |
| 429 | `{"error": "Rate limit exceeded"}` or `{"error": "Daily usage limit exceeded."}` |
| 500 | `{"error": "Background removal failed: ..."}` |

---

### `POST /api/v1/remove-bg/bulk`

Start an asynchronous bulk background-removal job. All images are uploaded in a single request and processed server-side in a background thread.

- **Method:** `POST`
- **URL:** `/api/v1/remove-bg/bulk`
- **Authentication:** `@auth_required(api_mode=True, enforce_usage=True)` + `@rate_limit_per_user`
- **Required Headers:** `Content-Type: multipart/form-data`

**Request Parameters**

| Field | Type | Required | Default | Validation |
|---|---|---|---|---|
| `images` | `file[]` | Yes | — | Each file extension must be `.jpg`, `.jpeg`, `.png`, or `.webp` |
| `resolution` | `string` | No | `"hd"` | Must be `"hd"` or `"standard"`; invalid values fall back to `"hd"` |

**Limits**

| Limit | Non-Admin | Admin |
|---|---|---|
| Max files per batch | 20 | Unlimited |
| Max file size | 10 MB | Unlimited |

**Example Request**

```bash
curl -X POST http://localhost:5001/api/v1/remove-bg/bulk \
  -H "X-API-Key: bg_abc123..." \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.png" \
  -F "resolution=standard"
```

**Example Response** — `200 OK`

```json
{
  "batch_id": "a1b2c3d4e5f6...",
  "total": 2
}
```

**Response Fields**

| Field | Type | Description |
|---|---|---|
| `batch_id` | `string` | 32-character hex UUID identifying this batch |
| `total` | `integer` | Number of valid images accepted for processing |

**Processing Details**  
- Each image is processed sequentially using the same BiRefNet model.  
- Usage is incremented per successfully processed image (**non-admin only**).  
- Stale batches (older than 1 hour) are automatically cleaned up when a new batch is submitted.  
- If a single image fails, processing continues with the remaining images (no cascade failure).

**Error Responses**

| Status | Description |
|---|---|
| 400 | `{"error": "No image files provided."}` |
| 400 | `{"error": "Maximum 20 files per batch."}` (non-admin only) |
| 400 | `{"error": "Unsupported file type: ..."}` |
| 400 | `{"error": "File too large: ... (max 10MB)"}` (non-admin only) |
| 400 | `{"error": "No valid image files provided."}` |
| 401 | `{"error": "Authentication required"}` |
| 403 | `{"error": "User is blocked"}` |
| 429 | `{"error": "Rate limit exceeded"}` or `{"error": "Daily usage limit exceeded."}` |

---

### `GET /api/v1/remove-bg/bulk/{batch_id}/status`

Poll the current progress of a bulk processing job.

- **Method:** `GET`
- **URL:** `/api/v1/remove-bg/bulk/{batch_id}/status`
- **Authentication:** `@auth_required(api_mode=True, enforce_usage=False)` — session cookie or `X-API-Key` header

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `batch_id` | `string` | The batch ID returned by `POST /api/v1/remove-bg/bulk` |

**Example Request**

```bash
curl http://localhost:5001/api/v1/remove-bg/bulk/a1b2c3d4e5f6.../status \
  -H "X-API-Key: bg_abc123..."
```

**Example Response** — `200 OK`

```json
{
  "status": "processing",
  "total": 10,
  "completed": 4,
  "failed": 1,
  "pending": 5
}
```

**Response Fields**

| Field | Type | Description |
|---|---|---|
| `status` | `string` | `"processing"` while running, `"completed"` when done |
| `total` | `integer` | Total number of files in the batch |
| `completed` | `integer` | Number of files processed successfully |
| `failed` | `integer` | Number of files that failed |
| `pending` | `integer` | Number of files still waiting (`total - completed - failed`) |

**Error Responses**

| Status | Description |
|---|---|
| 401 | `{"error": "Authentication required"}` |
| 404 | `{"error": "Batch not found"}` — batch expired or never existed |

---

### `GET /api/v1/remove-bg/bulk/{batch_id}/download`

Download a ZIP archive containing all successfully processed images from a completed batch. Each file is named `{original_stem}_processed.png`.

- **Method:** `GET`
- **URL:** `/api/v1/remove-bg/bulk/{batch_id}/download`
- **Authentication:** `@auth_required(api_mode=True, enforce_usage=False)` — session cookie or `X-API-Key` header

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `batch_id` | `string` | The batch ID returned by `POST /api/v1/remove-bg/bulk` |

**Example Request**

```bash
curl -OJ http://localhost:5001/api/v1/remove-bg/bulk/a1b2c3d4e5f6.../download \
  -H "X-API-Key: bg_abc123..."
```

**Example Response**

- **Status:** `200 OK`
- **Content-Type:** `application/zip`
- **Content-Disposition:** `attachment; filename="processed_images.zip"`
- **Body:** ZIP binary stream

**Processing**  
- On download, the temporary directory and the in-memory batch entry are deleted immediately.  
- Subsequent requests for the same `batch_id` return `404`.

**Error Responses**

| Status | Description |
|---|---|
| 400 | `{"error": "Batch not yet completed"}` |
| 401 | `{"error": "Authentication required"}` |
| 404 | `{"error": "Batch not found"}` — already downloaded, expired, or never existed |

---

## User Management APIs

All user management is handled via the authentication endpoints (`/signup`, `/login`, `/logout`, `/me`) documented in [Authentication APIs](#authentication-apis).

There is no dedicated admin-only user management API beyond block/unblock (see [Admin APIs](#admin-apis)).

### User Permissions Matrix

| Feature | `user` | `admin` |
|---|---|---|
| Single image processing | Yes (counts against daily limit) | Yes (unlimited) |
| Bulk processing | Yes (max 20 files, 10 MB each) | Yes (no limits) |
| API rate limit | 30 req/min | Exempt |
| Daily usage cap | Configurable (default 20) | Exempt |
| Session login | Yes | Yes |
| API key auth | Yes | Yes |
| `/admin` dashboard | No | Yes |
| Block/unblock users | No | Yes |

---

## Admin APIs

---

### `GET /admin`

Render the admin dashboard showing all registered users with their usage stats and block status.

- **Method:** `GET`
- **URL:** `/admin`
- **Authentication:** `@admin_required` — session required, role must be `"admin"`

**Example Request**

```bash
curl http://localhost:5001/admin \
  -b "session=..."
```

**Response:** `200 OK` — HTML page (`admin.html`)

The table displays:

| Column | Description |
|---|---|
| Username | User's login name |
| Role | `"user"` or `"admin"` |
| API Key | Truncated API key in `<code>` |
| Today | `today_usage` (or `"—"` for admins) |
| Total | `total_usage` (or `"—"` for admins) |
| Remaining | `remaining_usage` (or `"Unlimited"` for admins) |
| Status | `"Active"` or `"Blocked"` |
| Action | Block/Unblock button (non-admins) or `Admin` badge |

**Error Responses**

| Status | Description |
|---|---|
| 302 | Redirect to `/login` — not authenticated |
| 403 | `{"error": "Admin access required"}` — user exists but role is not `admin` |

---

### `POST /admin/toggle-block/{username}`

Block or unblock a non-admin user.

- **Method:** `POST`
- **URL:** `/admin/toggle-block/{username}`
- **Authentication:** `@admin_required` — session required, role must be `"admin"`

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `username` | `string` | The username to block or unblock |

**Example Request**

```bash
curl -X POST http://localhost:5001/admin/toggle-block/johndoe \
  -b "session=..."
```

**Response:** `302 Found` — redirects to `/admin` with a flash message.

**Guards (flash messages)**

| Condition | Message |
|---|---|
| Target user does not exist | `"User '...' not found."` |
| Target user is an admin | `"Cannot block another admin."` |
| Admin targets themselves | `"Cannot block yourself."` |
| Success | `"User '...' blocked."` or `"User '...' unblocked."` |

**Error Responses**

| Status | Description |
|---|---|
| 302 | Redirect to `/login` — not authenticated |
| 403 | `{"error": "Admin access required"}` — non-admin user |

---

## File Upload Specifications

| Property | Single Upload | Bulk Upload (non-admin) | Bulk Upload (admin) |
|---|---|---|---|
| **Supported formats** | `.jpg`, `.jpeg`, `.png`, `.webp` | `.jpg`, `.jpeg`, `.png`, `.webp` | `.jpg`, `.jpeg`, `.png`, `.webp` |
| **Max file size** | 10 MB | 10 MB per file | Unlimited |
| **Max files per request** | 1 | 20 | Unlimited |
| **Request format** | `multipart/form-data` | `multipart/form-data` | `multipart/form-data` |
| **Field name** | `image` | `images` (repeated) | `images` (repeated) |

**Storage Behavior**  
- Uploaded files are read into memory, validated, then passed directly to the model.  
- For bulk jobs, processed PNGs are written to a temporary directory (`tempfile.mkdtemp`).  
- No permanent storage on disk beyond the temp directory.

**Cleanup Policies**  
- **Single upload:** Result streamed directly to the client; no cleanup needed.  
- **Bulk upload:**  
  - Temp files are cleaned up immediately when the ZIP is downloaded.  
  - Orphaned batches (no download within 1 hour) are cleaned up on the next bulk submission.  
  - All batch state is in-memory and lost on server restart.

---

## Response Status Codes

| Code | Name | Usage |
|---|---|---|
| `200` | OK | Successful JSON response, image/ZIP download, or HTML page |
| `302` | Found | Redirect after login/logout/block action |
| `400` | Bad Request | Missing or invalid parameters (file, filename, extension, size) |
| `401` | Unauthorized | Missing or invalid authentication |
| `403` | Forbidden | Account blocked, or non-admin accessing admin route |
| `404` | Not Found | Batch ID not found (expired or never existed) |
| `429` | Too Many Requests | Rate limit exceeded or daily usage cap reached |
| `500` | Internal Server Error | Model inference failure or unexpected exception |

---

## API Flow Diagrams

### 1. User Authentication

```
Browser                          Server
   │                                │
   ├── GET /login ──────────────────►  Render login.html
   │◄──────── 200 OK ──────────────┤
   │                                │
   ├── POST /login (username/pass) ─►  Verify bcrypt hash
   │                                ├── success: set session cookie
   │◄──────── 302 → /app ──────────┤
   │                                │
   │       (all subsequent requests carry session cookie)
   │                                │
   ├── GET /app ───────────────────►  @auth_required validates session
   │◄────── 200 OK (index.html) ───┤
```

### 2. Single Image Processing

```
   Client                         Server                        Model
     │                              │                             │
     ├─ POST /api/v1/remove-bg ────► │                             │
     │   (multipart: image +       │                             │
     │    resolution)              │                             │
     │                              ├─ @auth_required            │
     │                              │  - resolve user            │
     │                              │  - check blocked           │
     │                              │  - check usage cap         │
     │                              ├─ @rate_limit_per_user      │
     │                              │  - check 60s sliding window│
     │                              ├─ validate file type/size   │
     │                              ├─ remove_background() ─────►│
     │                              │       open PIL Image       │
     │                              │       preprocess (resize,  │
     │                              │        normalize)          │
     │                              │       model(input_tensor)  │
     │                              │       sigmoid → mask       │
     │                              │       postprocess → RGBA   │
     │                              │◄──── PNG bytes ───────────┤
     │                              ├─ update_usage (non-admin)  │
     │                              ├─ attach usage headers      │
     │◄──── 200 OK (image/png) ─────┤                             │
     │      + X-Usage-* headers    │                             │
```

### 3. Bulk Image Processing

```
   Client                         Server                        Model
     │                              │                             │
     ├─ POST /api/v1/remove-bg/   │                             │
     │   bulk                     │                             │
     │   (multipart: images[] +   │                             │
     │    resolution)             │                             │
     │                              ├─ validate (auth, rate,    │
     │                              │   files, types, sizes)    │
     │                              ├─ create temp dir          │
     │                              ├─ store batch info         │
     │                              ├─ start daemon thread      │
     │◄──── 200 OK {batch_id, ─────┤                             │
     │       total}                │                             │
     │                              │                             │
     │       ┌─── [background thread] ───────────────────────────┤
     │       │   for each file:                                 │
     │       │     remove_background() ────────────────────────► │
     │       │     save _processed.png to temp dir              │
     │       │     update_usage (non-admin)                     │
     │       │     update batch progress (completed/failed)     │
     │       │   set status = "completed"                       │
     │       └───────────────────────────────────────────────────┤
     │                              │                             │
     ├─ GET .../bulk/{id}/status ──► │ (polled every ~1s)        │
     │◄─── {status, completed, ─────┤                             │
     │       failed, pending}       │                             │
     │                              │                             │
     │       (wait for status == "completed")                    │
     │                              │                             │
     ├─ GET .../bulk/{id}/download ► │                             │
     │                              ├─ verify completed          │
     │                              ├─ build ZIP in memory       │
     │                              ├─ delete temp dir           │
     │                              ├─ remove batch from store   │
     │◄──── 200 OK (application/zip)─┤                           │
```

### 4. ZIP Generation and Download

```
Server-side (on GET /download)
─────────────────────────────────
  1. Verify batch exists and status == "completed"
  2. Create io.BytesIO buffer
  3. Open zipfile.ZipFile(buffer, ZIP_DEFLATED)
  4. For each .png file in temp_dir (sorted by name):
       zf.write(file, arcname=file.name)
  5. Close ZIP
  6. Seek buffer to 0
  7. Delete temp directory (shutil.rmtree)
  8. Remove batch from in-memory _batches dict
  9. Return send_file(buffer, mimetype="application/zip",
         as_attachment=True, download_name="processed_images.zip")
```

---

## Security Notes

### Authentication Requirements
- Every API route except `/signup`, `/login`, `/logout`, and `/` requires authentication.
- Two mutually compatible methods: session cookie (browser) and `X-API-Key` header (programmatic).
- Session takes priority when both are supplied; a mismatched API key on a session-authenticated request counts as a failed attempt.

### Permission Checks (RBAC)
- **`@auth_required`** — resolves the user, checks `is_blocked`, optionally checks `remaining_usage > 0`.
- **`@admin_required`** — resolves the user, verifies `role == "admin"`, blocks all other roles with `403`.
- Role checks happen server-side on **every** request to protected endpoints. Frontend role indicators are purely cosmetic.

### Admin Bypass Rules

| Check | Admin Behavior |
|---|---|
| Usage cap (`enforce_usage=True`) | Skipped entirely in `@auth_required` |
| Rate limiting (`@rate_limit_per_user`) | Returns immediately without tracking |
| Usage increment (`update_usage()`) | Returns user document unchanged |
| Usage response headers | `X-Usage-Used: 0`, `X-Usage-Limit: Unlimited`, `X-Remaining-Usage: Unlimited` |
| Max bulk files | Not enforced |
| Max file size | Not enforced |
| Block/unblock | Cannot block self or other admins |

### Input Validation
- **Username:** 3–30 characters, only `[A-Za-z0-9_]` — enforced via `valid_username` regex validator.
- **Password:** Minimum 6 characters — enforced via `valid_password` validator.
- **File extensions:** Whitelist `{.jpg, .jpeg, .png, .webp}` — checked server-side.
- **Resolution:** Enum `{hd, standard}` — defaults to `hd` for invalid values.
- **Batch ID:** 32-character hex UUID — provided by server, not user-supplied.

### File Validation
- Maximum file size: 10 MB for non-admin users; unlimited for admins.
- Content type is inferred from file extension, not MIME type.
- Empty filenames are rejected.

### Rate Limiting Policies
- Sliding 60-second window, in-memory (`defaultdict[deque]` + `threading.Lock`).
- Keyed by MongoDB `_id` of the authenticated user.
- Default limit: 30 requests per minute (configurable via `RATE_LIMIT_PER_MINUTE` env var).
- **Limitation:** Rate limit state is lost on server restart.

### Additional Security Measures
- **Session:** `HttpOnly`, `SameSite=Lax`, configurable `Secure` flag, 1-day lifetime.
- **Password storage:** Bcrypt with auto-generated salt via `werkzeug.security`.
- **API key generation:** `secrets.token_urlsafe(24)` — cryptographically random.
- **Auto-block:** Account blocked after `FAILED_ATTEMPTS_THRESHOLD` (default 5) consecutive failed API key mismatches on a session-authenticated request.

---

## Configuration Reference

All configuration is loaded from environment variables (`.env` file supported via `python-dotenv`).

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | (required) | Flask secret key for session signing |
| `MONGO_URI` | (required) | MongoDB connection string |
| `MONGO_DB_NAME` | `bg_saas` | MongoDB database name |
| `USER_DAILY_USAGE_LIMIT` | `20` | Daily API calls for regular users |
| `ADMIN_DAILY_USAGE_LIMIT` | `50` | Daily API calls for admins |
| `FAILED_ATTEMPTS_THRESHOLD` | `5` | Failed attempts before auto-block |
| `RATE_LIMIT_PER_MINUTE` | `30` | Max API requests per minute per user |
| `ADMIN_USERNAME` | (optional) | Auto-create admin on startup |
| `ADMIN_PASSWORD` | (optional) | Password for auto-created admin |

---

## Changelog

### v1.0 (2025-06-09)
- Initial release.
- Single image background removal (`POST /api/v1/remove-bg`).
- Bulk background removal with async processing (`POST /api/v1/remove-bg/bulk`).
- Batch status polling (`GET .../status`).
- Batch ZIP download (`GET .../download`).
- User registration and session-based / API-key authentication.
- Admin dashboard with user block/unblock.
- Role-based access control with admin bypass of all limits.
- Rate limiting (30 req/min/user).
- Daily usage tracking with automatic reset.
