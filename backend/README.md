# Backend — JustCorp Labs AI Knowledge Base Chatbot

FastAPI backend for the JustCorp Labs RAG chatbot.

## Purpose

This backend powers the AI Knowledge Base Chatbot. It handles document upload, PDF text extraction, chunking, embeddings, ChromaDB storage, semantic search, and Groq-powered answer generation.

## Features

- PDF upload
- PDF text extraction
- Text cleaning
- Text chunking
- Metadata generation
- Local embeddings with sentence-transformers
- ChromaDB vector storage
- Semantic retrieval
- Groq LLM answer generation
- Source-aware responses
- Explicit route authorization; public API documentation disabled

## Tech Stack

- Python
- FastAPI
- Uvicorn
- PyMuPDF
- sentence-transformers
- ChromaDB
- Groq
- python-dotenv
- Pydantic

## Folder Structure

```text
backend/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── document_loader.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── rag_pipeline.py
│   ├── llm_client.py
│   └── models.py
│
├── uploads/
├── chroma_db/
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

Create virtual environment:

```powershell
python -m venv .venv
```

Activate virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Environment Variables

Create `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Required variables:

```env
GROQ_API_KEY=
LLM_PROVIDER=groq
MODEL_NAME=llama-3.1-8b-instant
CHROMA_DB_PATH=./chroma_db
UPLOAD_DIR=./uploads
FRONTEND_ORIGIN=http://localhost:5173
```

Do not commit the real `.env` file to GitHub. Replace example credential placeholders privately before running the relevant integration.

| Variable | Purpose / requirement |
| --- | --- |
| `GROQ_API_KEY` | Private API credential; required for Groq answers. |
| `LLM_PROVIDER` | Provider selection. |
| `MODEL_NAME` | Model selection. |
| `CHROMA_DB_PATH` | Local vector storage path. |
| `UPLOAD_DIR` | Local upload path. |
| `FRONTEND_ORIGIN` | Allowed frontend origin. |
| `WHATSAPP_ACCESS_TOKEN` | Private access token; required for WhatsApp messaging. |
| `WHATSAPP_PHONE_NUMBER_ID` | Phone identifier; required for WhatsApp messaging. |
| `WHATSAPP_VERIFY_TOKEN` | Private, unique webhook verification token; required for WhatsApp setup. |

The frontend uses `VITE_API_BASE_URL` for its public backend URL. Never put secrets in `VITE_` variables: they are exposed to the browser.

From the repository root, run `python scripts/check_secret_hygiene.py` before committing. The check reads tracked working-tree files and example configuration only; it does not load local `.env` files or print matched values. It checks example keys, credential placeholders, common credential signatures, and ignore rules. It is a focused guard, not a complete secret scanner or Git history audit.

Run `python scripts/check_secret_hygiene.py --self-test` for isolated synthetic regression fixtures, including error-output disclosure checks. Tests create temporary Git repositories and do not change application configuration. Missing or unreadable files, invalid Python configuration, malformed examples, unsupported text encodings, and Git failures produce controlled diagnostics and a nonzero exit code. Diagnostics use generic rule identifiers; filenames, subprocess output and exception details are never printed. Files over 1 MiB fail closed. Python configuration is limited to 64 Ki characters and 512 punctuation characters, and 2,048 lexical tokens before AST parsing; parser memory and recursion failures also fail closed.

Text scanning supports strict UTF-8 (with an optional BOM) and BOM-marked UTF-16. Other encodings, embedded NULs, and malformed text fail closed. PNG and JPEG files with matching extensions and format signatures are excluded from text scanning; their embedded metadata is not scanned. Detection includes AWS permanent and temporary access-key IDs, common provider prefixes, private-key headers, credential URLs, and literal token/key/secret/password assignments of at least 16 characters. Unprefixed assignment detection is limited to letters, digits, underscores, slashes, plus, minus, and equals; computed values, dotted tokens, shorter arbitrary secrets, archives, and image contents require separate review. Environment examples additionally require empty credential values or `your_..._here` placeholders. Public `.pub` keys and environment examples remain trackable; PEM names containing private/Private/PRIVATE and private key bundles remain ignored. Other PEM files may be tracked only with complete PUBLIC KEY, RSA PUBLIC KEY, or CERTIFICATE envelopes; ambiguous or private PEM content fails the scanner. This envelope classification does not validate cryptographic authenticity.

Security follow-up: `app/config.py` currently contains a static fallback for `WHATSAPP_VERIFY_TOKEN`. Set a unique private environment value when configuring WhatsApp. Removing that fallback requires a separately authorised authentication change.

Replacing tracked values does not revoke credentials or remove them from existing Git history. Any previously exposed credential requires an owner-managed revocation/rotation review; this task does not rotate credentials or rewrite history.

## Run Backend

```powershell
uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Swagger, ReDoc, and OpenAPI endpoints are disabled (404).

## Main Endpoints

Optional routes are disabled by default:

- `ENABLE_WHATSAPP_ROUTES=false` controls GET/POST `/whatsapp/webhook` and POST `/whatsapp/send-test`.
- `ENABLE_TEST_ANSWER_ROUTE=false` controls POST `/test-answer`.

Only `true` (case insensitive, surrounding whitespace allowed) enables a flag.
Missing, empty, false, 0, and unrecognized values keep it disabled. Flags are
read at startup; restart the backend after changing them. Disabled routes return
404 and are excluded from OpenAPI. With WhatsApp disabled, its modules are not
imported and its credentials are not required.

Both WhatsApp routes and the /test-answer debugging endpoint must remain disabled in public deployments until their respective authentication, authorization, and security controls have been implemented and independently verified.
Enabled optional routes require administrator authorization; flags never bypass authorization.

Run isolated route tests from the repository root with the backend environment:

```powershell
.\backend\.venv\Scripts\python.exe -B -m unittest discover -s backend/tests -v
```

Tests use temporary storage and mocked providers; no Groq or Meta calls are made.
They require FastAPI's test client dependency `httpx`, declared in
`requirements-test.txt`, in the test environment.

### Health Check

```http
GET /health
```

### Upload Document

```http
POST /upload-document
```

### List Documents

```http
GET /documents
```

### Delete Document

```http
DELETE /documents/{document_id}
```

### Search Documents

```http
POST /search
```

### Ask Question

```http
POST /ask
```

## Notes

Version 1 supports PDF files first.

TXT, DOCX, OCR, and website ingestion can be added later.


## SEC03-02A PostgreSQL configuration foundation

Development uses local PostgreSQL under the USD 0/month policy. No PostgreSQL,
Docker, packages, or managed services are installed by this change. Managed hosting
and identity providers remain deferred. Render remains suspended. Authentication
is still deliberately locked out; no database connection, engine, session, schema,
or migration is created. Existing application configuration is unchanged.

`app.database_config.load_database_settings()` reads backend process environment
only, on demand. Importing the module does nothing. Missing or invalid settings
raise `DatabaseConfigurationError` when explicitly validated, while public health
remains available. Every future database-dependent authentication operation must
validate through this function before database access; no such operation exists yet.
The loader does not discover `.env` files: a future backend entry point must load
the intended backend environment before calling it. Never use frontend `VITE_`
variables for database configuration.

| Variable | Default / validation |
| --- | --- |
| `DATABASE_ENVIRONMENT` | `development`; exactly `development`, `test`, or `production` |
| `DATABASE_URL` | Empty; required on validation, `postgresql+psycopg` only, explicit host, user and database |
| `DATABASE_SSLMODE` | `verify-full`; only `verify-full` or explicit local development/test `disable` |
| `DATABASE_SSLROOTCERT` | Empty; readable, nonempty absolute CA file required for `verify-full` |
| `DATABASE_CONNECT_TIMEOUT` | 5 seconds; integer 1–30 |
| `DATABASE_POOL_SIZE` | 2; integer 1–5; future engine must use `max_overflow=0` |
| `DATABASE_POOL_TIMEOUT` | 5 seconds; integer 1–30 for future pool acquisition |

Placeholder URI: `postgresql+psycopg://your_user_here@localhost:5432/knowledge_hub`.
Set credentials privately when local persistence is implemented; percent-encode
reserved characters. URI query strings and fragments are rejected to prevent
driver, TLS, host, and timeout overrides. Database names are restricted to ASCII
letters, digits, underscores and hyphens. Plain `postgresql://` is rejected because
it does not explicitly select Psycopg 3. Local plaintext requires an explicit
`DATABASE_SSLMODE=disable` and literal `localhost`, `127.0.0.1`, or `::1` host.

Production always requires `verify-full` plus the CA file: the future driver must
verify both the certificate chain and hostname and pass these settings explicitly.
The validator checks file availability, not certificate authenticity or server
identity; those require an actual TLS handshake in a later task. Future engine
integration must also pass both timeout values, bound the pool, and avoid logging
connection arguments. Errors and settings representations redact supplied values;
`settings.uri` now contains immutable validated components, with redacted
`str`/`repr`, rather than the original input string. Future SQLAlchemy integration
must pass its decoded fields directly to `URL.create(drivername=..., username=...,
password=..., host=..., port=..., database=...)`; do not decode again or reparse a
string. Explicit `render_as_string(hide_password=False)` exports a sensitive URI
with percent-encoded credentials; default rendering hides the password. Individual
credential attributes and dataclass serialization remain sensitive.

Validated database configuration contains sensitive credential fields. The settings
object and SQLAlchemy URLs must only be handled by trusted backend code. Direct
field access, dataclass serialization (such as dataclasses.asdict()), and
unredacted URL rendering may disclose credentials. Database URLs and passwords
must never be written to logs, responses, frontend variables, or exception
messages. Use redacted representations for diagnostics.

The hygiene scanner retains its original configuration limits, with a bounded
2,048 punctuation / 4,096 token allowance for this larger database module only;
its 64 Ki character limit and fail-closed parser handling remain in force.

FIX01 uses a conservative grammar reviewed against SQLAlchemy 2.0.44's
[`_parse_url` source](https://github.com/sqlalchemy/sqlalchemy/blob/rel_2_0_44/lib/sqlalchemy/engine/url.py).
Only lowercase literal schemes and DNS hosts, canonical bracketed IPv6, explicit
nonempty decimal ports (1-65535, no leading zeros), and unreserved or correctly
percent-encoded credential characters are accepted. Credentials are decoded once
with strict UTF-8 and control characters rejected. Extra unescaped `@`, malformed
escapes, queries and fragments fail closed. Local plaintext eligibility uses the
validated host component. SQLAlchemy 2.0.44 was installed locally for development
testing, and offline URL.create() compatibility tests passed. These checks do not
establish that all production dependencies are installed or that a database
connection has been tested; runtime driver integration remains untested. The tester's literal ambiguous URI
was not supplied; regressions cover multiple extra-`@` authority variants.

Optional dependencies are isolated in `requirements-database.txt`:
`SQLAlchemy==2.0.44`, `psycopg[binary]==3.2.10`, `alembic==1.16.5`.
The binary extra avoids requiring a locally installed libpq for a future approved
Windows development installation. These releases support the inspected Python
3.13 environment (Alembic requires Python 3.9+); no existing runtime requirements
are changed. Direct versions are pinned; this is not a fully locked transitive
environment. Driver wheel availability and combined dependency resolution with
FastAPI/Pydantic and the existing unpinned backend requirements must be verified
in an independently approved installation. The configuration module itself uses
only the Python standard library. The configuration test module imports existing
FastAPI/httpx-based route fixtures, so running the test module requires those
test dependencies. SQLAlchemy URL compatibility tests are skipped when SQLAlchemy
is unavailable or its installed version is not the expected 2.0.44; source-contract
checks still run. No packages were installed for this task.

Run configuration tests from the repository root:
`backend\.venv\Scripts\python.exe -B -m unittest discover -s backend/tests -p test_database_config.py -v`.

## SEC03-01 access boundary

Production intentionally denies every protected request with 401. There is no
functional login, session verification, token issuance, shared API key, or
authentication-disable flag. Headers, cookies, query parameters, request bodies,
and frontend roles cannot establish identity. Do not release this phase to
production as a functioning authenticated product. Verified session infrastructure
and independent security verification are required before production release.

| Method | Path | Access |
| --- | --- | --- |
| GET | `/`, `/health` | Public, minimal status only |
| GET | `/documents` | Active verified member or administrator |
| POST | `/search`, `/ask` | Active verified member or administrator |
| POST | `/upload-document` | Active verified administrator |
| DELETE | `/documents/{document_id}` | Active verified administrator |
| POST | `/test-answer` | Administrator, only when explicitly enabled |
| GET, POST | `/whatsapp/webhook` | Administrator, only when explicitly enabled |
| POST | `/whatsapp/send-test` | Administrator, only when explicitly enabled |

Missing or malformed verified identity receives 401; inactive identities and
members attempting administrator operations receive 403. Disabled optional
routes and documentation endpoints receive 404. Authorized handlers retain their
existing validation and missing-document responses. Invalid request syntax can
be rejected by FastAPI before authorization, so 401 is not guaranteed for every
malformed HTTP body.

The immutable internal Principal requires a nonempty identifier, an explicit
boolean active status, and exactly `member` or `admin`. Tests alone override
`resolve_verified_principal` through FastAPI dependency overrides, using synthetic
principals, temporary storage, and mocked providers. Overrides are cleared after
use; the production resolver then rejects again. Never configure such overrides
in deployment code.

Service imports occur inside protected handlers. Startup, public health, and
denied requests do not initialize Groq or document storage, perform retrieval,
embeddings, PDF extraction, LLM generation, application upload-file creation, or
WhatsApp messaging. FastAPI may parse request bodies before dependencies execute:
this protection does not prevent framework multipart buffering or temporary-file
spooling. Request-size and ingress resource controls remain separate work.

WhatsApp remains default-disabled and quarantined behind administrator checks,
including webhook verification. Meta cannot complete a normal webhook workflow
in this phase. A webhook verification token is not application authentication.
The debug route also remains default-disabled. Startup validates every registered
route against an explicit policy inventory and rejects missing guards or unknown
routes. Any future route additions must update and test that inventory.
