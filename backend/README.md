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

Do not commit the real `.env` file to GitHub.

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