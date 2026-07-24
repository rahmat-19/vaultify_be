# Vaultify — Secure Password Vault API

Production-oriented FastAPI backend for mobile password-vault clients. It uses
Argon2id password hashing, short-lived JWT access tokens, rotating opaque refresh
tokens, ownership-scoped repositories, and AES-256-GCM authenticated encryption.

## Security model

- Passwords are hashed with Argon2id and are never recoverable.
- Vault passwords, API keys (stored in `password` with category `api_key`), and
  secure notes are encrypted before persistence.
- AES-GCM uses a fresh random 96-bit nonce for every field encryption.
- Refresh tokens are high-entropy opaque values; only SHA-256 digests are stored.
- Refresh tokens rotate on use and are explicitly revoked at logout.
- Every vault query includes the authenticated user's ID. Foreign item IDs return
  404 to avoid leaking their existence.
- Accounts lock for 15 minutes after five consecutive failed login attempts.
- Access-token expiration provides session timeout; the default is 15 minutes.
- Validation, restricted CORS/hosts, rate limits, security headers, generic 500
  errors, and secret-aware logging provide defense in depth.

Keep the encryption key in a secrets manager in production. Losing it makes vault
data unrecoverable; exposing it compromises all encrypted fields. TLS termination
is required in production.

## Requirements

- Python 3.13
- SQLite 3 (development)
- Docker and Docker Compose (optional)

## Local installation

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Generate secrets and put their outputs in `.env`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

Replace `JWT_SECRET_KEY` with the first value and `ENCRYPTION_KEY` with the
second. Do not commit `.env`.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `ENVIRONMENT` | `development`, `testing`, or `production` | `development` |
| `DEBUG` | FastAPI debug behavior | `false` |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./vaultify.db` |
| `JWT_SECRET_KEY` | JWT HMAC key, minimum 32 characters | required |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token/session lifetime | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh-session lifetime | `30` |
| `ENCRYPTION_KEY` | URL-safe base64 encoding of 32 random bytes | required |
| `CORS_ORIGINS` | Comma-separated allowed origins | localhost web client |
| `ALLOWED_HOSTS` | Comma-separated HTTP host allowlist | local/test hosts |
| `RATE_LIMIT_LOGIN` | Per-IP login rate | `5/minute` |
| `ACCOUNT_LOCK_MINUTES` | Lockout duration after five failures | `15` |
| `LOG_LEVEL` | Application logging level | `INFO` |
| `LOG_FILE` | Rotating application log path | `logs/app.log` |
| `LOG_MAX_BYTES` | Maximum size of each log file | `5242880` |
| `LOG_BACKUP_COUNT` | Number of rotated log files retained | `5` |

## Database migrations

```bash
alembic upgrade head
```

Create a migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Run the server

```bash
uvicorn app.main:app --reload
```

Health check: `GET http://localhost:8000/health`

Interactive OpenAPI documentation is available in non-production environments:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

All business endpoints return:

```json
{"success": true, "message": "Operation completed", "data": {}}
```

Errors use:

```json
{"success": false, "message": "Request validation failed", "errors": []}
```

Send access tokens as `Authorization: Bearer <access_token>`. Mobile clients
should keep tokens in OS secure storage and must never log them.

## API endpoints

| Method | Path | Authentication |
|---|---|---|
| POST | `/api/v1/auth/register` | No |
| POST | `/api/v1/auth/login` | No |
| POST | `/api/v1/auth/refresh` | No (refresh token body) |
| POST | `/api/v1/auth/logout` | Access + refresh token |
| GET | `/api/v1/auth/me` | Access token |
| GET | `/api/v1/vault` | Access token |
| GET | `/api/v1/vault/search?q=term` | Access token |
| GET | `/api/v1/vault/{id}` | Access token |
| POST | `/api/v1/vault` | Access token |
| PUT | `/api/v1/vault/{id}` | Access token |
| DELETE | `/api/v1/vault/{id}` | Access token |

Search deliberately covers only unencrypted metadata: title, username, website,
and category. Searching plaintext notes/passwords would require decrypting every
record and is intentionally excluded.

## Docker

Create `.env` first, then:

```bash
docker compose up --build
```

The container runs migrations before startup, uses a non-root user, and stores the
SQLite database in the `vaultify_data` volume.

## Tests and code quality

```bash
pytest
pytest --cov=app --cov-report=term-missing
ruff check .
black --check .
pre-commit install
pre-commit run --all-files
```

Tests cover registration, duplicate validation, login, `/me`, refresh rotation,
logout revocation, unauthorized access, vault CRUD/search, cross-user isolation,
ciphertext-at-rest, nonce uniqueness, tamper detection, password policy, and URL
validation.

## Folder structure

```text
app/
├── api/             # Routers and dependency wiring
├── core/            # Configuration, errors, logging, rate limiting
├── database/        # SQLAlchemy base, engine, sessions
├── middleware/      # HTTP security headers
├── models/          # SQLAlchemy ORM entities
├── repositories/    # Persistence and ownership-scoped queries
├── schemas/         # Pydantic v2 request/response contracts
├── security/        # Argon2, JWT, refresh tokens, AES-GCM
├── services/        # Business use cases
├── tests/           # Unit and API integration tests
└── utils/           # Shared utility namespace
alembic/             # Versioned database migrations
```

## Production checklist

- Use a managed PostgreSQL database and a production ASGI process manager.
- Store JWT/encryption keys in a managed secret store and define a rotation plan.
- Terminate TLS at a trusted load balancer and restrict `ALLOWED_HOSTS`/CORS.
- Back up both the database and encryption key separately and test restoration.
- Centralize scrubbed logs and monitoring; alert on lockouts and abnormal rates.
- Run migrations as a dedicated deployment step when using multiple replicas.
