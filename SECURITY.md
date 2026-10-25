# Secret management and API key service

## Gemini key in the Streamlit app

Use **Settings → Gemini API** to save a local Gemini key. The application writes it to the machine's operating system credential store through `keyring`; it does not write the raw key to SQLite, a TOML file, or the application database. The Settings page displays only the first four characters and `###`. The password input clears after submission. Gemini calls read the key only when needed. Configure a deployed instance with `GEMINI_API_KEY` from the hosting platform's secret manager instead of a local keychain. Never commit a real key or place one in `.env`.

## Optional internal API service

`api_service.py` is a separate FastAPI service; Streamlit itself does not expose these routes. Install dependencies with `pip install -r requirements.txt`. Configure these values through a deployment secret manager before starting it:

- `API_KEY_PEPPER`: at least 32 random bytes, kept stable and private; changing it invalidates all issued keys.
- `API_KEY_ADMIN_TOKEN`: at least 32 random bytes; required to manage issued keys.
- `API_KEY_DB_PATH`: optional path to the SQLite key database.

Generate deployment secrets with a platform secret manager or a secure generator. Do not print them into CI logs. Start the service with `uvicorn api_service:app --host 127.0.0.1 --port 8000` behind an HTTPS reverse proxy. Bind to a private interface and restrict access to the admin routes at the network layer as well.

Admin routes use `Authorization: Bearer <API_KEY_ADMIN_TOKEN>`:

- `POST /admin/api-keys` creates a key. The raw key appears only in this response; capture it securely because it cannot be retrieved later.
- `GET /admin/api-keys` lists metadata only.
- `PATCH /admin/api-keys/{id}` updates name, scopes, rate limit, active status, or expiry.
- `DELETE /admin/api-keys/{id}` revokes a key; `/permanent` deletes its record.

Routes under `/internal/` require an issued key in `Authorization: Bearer <key>` or `X-API-Key`. The middleware validates the token, active state and expiry, enforces the stored per-minute quota, and attaches the identity and scopes to `request.state`. The sample `/internal/whoami` endpoint requires `read:self`.

The database stores an HMAC-SHA-256 digest keyed by `API_KEY_PEPPER`; issued key secrets contain 256 bits of cryptographically secure randomness. Verification compares fixed-size digests in constant time. Never log authorization headers, raw keys, admin tokens, or request bodies containing credentials. Rotate keys by issuing replacements, updating clients, then revoking old keys.

The included service uses SQLite and per-minute database counters, suitable for a single host or local deployment. A multi-instance production deployment should move this schema and rate-limit accounting to a managed shared database/cache, add operational monitoring that redacts credentials, and provision backups and access controls for that infrastructure.
