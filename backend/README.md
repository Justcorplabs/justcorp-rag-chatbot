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
- FastAPI Swagger documentation

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

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

## Main Endpoints

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
