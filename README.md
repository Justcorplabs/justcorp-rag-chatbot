# JustCorp Labs AI Knowledge Base Chatbot

A professional RAG chatbot demo built by **JustCorp Labs**.

This project turns uploaded business documents into a searchable AI knowledge base. Users can upload PDF documents and ask questions. The chatbot retrieves relevant document context and generates answers using only the uploaded documents.

## Project Purpose

The goal of this project is to demonstrate how JustCorp Labs builds practical AI systems for business growth.

This chatbot can be used for:

- Customer support knowledge bases
- Staff onboarding
- Internal training
- Business FAQs
- Service guides
- Policy documents
- Faster decision-making
- Document search and summarisation

Core message:

> We built an AI assistant that helps businesses turn their own documents into a searchable knowledge base for customer support, onboarding, internal training, and faster decision-making.

## What is RAG?

RAG means **Retrieval-Augmented Generation**.

Instead of asking an AI model to answer from memory, the system first searches uploaded documents, retrieves the most relevant sections, and then asks the language model to answer using that context.

Simple flow:

```text
User question
    ↓
Question embedding
    ↓
Search ChromaDB
    ↓
Retrieve relevant document chunks
    ↓
Send context to LLM
    ↓
Return grounded answer with sources
```

This helps reduce hallucinations because the chatbot is instructed to answer only from the uploaded document context.

## Features

- PDF document upload
- PDF text extraction
- Text cleaning
- Text chunking with metadata
- Local embeddings using sentence-transformers
- ChromaDB vector storage
- Semantic document search
- Groq LLaMA answer generation
- FastAPI backend
- React frontend
- Uploaded document list
- Delete document from knowledge base
- Chat interface
- Source/context display
- JustCorp Labs branding
- Refusal behavior when answer is not found in uploaded documents

## Tech Stack

### Backend

- Python
- FastAPI
- Uvicorn
- PyMuPDF
- sentence-transformers
- all-MiniLM-L6-v2
- ChromaDB
- Groq API
- python-dotenv
- Pydantic

### Frontend

- React
- Vite
- JavaScript
- CSS
- lucide-react icons

### AI / RAG

- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Vector database: ChromaDB
- LLM provider: Groq
- Suggested model: `llama-3.1-8b-instant`

## Folder Structure

```text
justcorp-rag-chatbot/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── document_loader.py
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   ├── rag_pipeline.py
│   │   ├── llm_client.py
│   │   └── models.py
│   │
│   ├── uploads/
│   ├── chroma_db/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── public/
│   │   └── justcorp-logo.jpg
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── UploadPanel.jsx
│   │   │   ├── DocumentList.jsx
│   │   │   ├── ExampleQuestions.jsx
│   │   │   ├── ChatPanel.jsx
│   │   │   └── SourcePanel.jsx
│   │   │
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── main.jsx
│   │   └── styles.css
│   │
│   ├── package.json
│   ├── .env.example
│   └── README.md
│
├── demo_documents/
│   ├── justcorp_services_guide.txt
│   ├── justcorp_faq.txt
│   ├── justcorp_business_audit_guide.txt
│   └── justcorp_onboarding_guide.txt
│
├── screenshots/
├── README.md
└── .gitignore
```

## Backend Setup

Move into the backend folder:

```powershell
cd backend
```

Create virtual environment:

```powershell
python -m venv .venv
```

Activate virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks scripts:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Add your Groq API key inside `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq
MODEL_NAME=llama-3.1-8b-instant
CHROMA_DB_PATH=./chroma_db
UPLOAD_DIR=./uploads
FRONTEND_ORIGIN=http://localhost:5173
```

Run backend:

```powershell
uvicorn app.main:app --reload
```

Backend will run on:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Frontend Setup

Move into the frontend folder:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Create `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Frontend `.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Run frontend:

```powershell
npm run dev
```

Frontend will run on:

```text
http://localhost:5173
```

## API Endpoints

### Health Check

```http
GET /health
```

Checks whether the backend is running.

### Upload Document

```http
POST /upload-document
```

Uploads a PDF, extracts text, chunks it, creates embeddings, and stores it in ChromaDB.

### List Documents

```http
GET /documents
```

Returns documents stored in the knowledge base.

### Delete Document

```http
DELETE /documents/{document_id}
```

Deletes a document’s chunks from ChromaDB.

### Search Documents

```http
POST /search
```

Returns relevant document chunks without generating an LLM answer.

Example:

```json
{
  "question": "What is this document about?",
  "top_k": 4
}
```

### Ask Question

```http
POST /ask
```

Main chatbot endpoint. Retrieves relevant chunks and generates an answer using Groq.

Example:

```json
{
  "question": "What services does JustCorp Labs offer?",
  "top_k": 4
}
```

## System Prompt

The chatbot uses this grounding behavior:

```text
You are a helpful business knowledge assistant for JustCorp Labs.
Answer the user’s question using only the provided document context.
If the answer is not in the context, say that the uploaded documents do not contain enough information to answer.
Be clear, concise, and professional.
Do not make up facts.
```

## Demo Questions

After uploading the JustCorp Labs demo documents, try asking:

- What services does JustCorp Labs offer?
- What is a free business audit?
- Can JustCorp Labs build dashboards?
- What businesses does JustCorp Labs help?
- How does the onboarding process work?
- What problems can automation solve?
- How can AI help with customer support?
- What is included in the business audit?

## Screenshots

Add screenshots here after testing:

```text
screenshots/
├── homepage.png
├── upload-document.png
├── chat-answer.png
├── sources-panel.png
└── mobile-view.png
```

Suggested screenshots:

1. Full landing page
2. Upload section
3. Uploaded documents list
4. Chat answer with sources
5. Unsupported question refusal
6. Mobile responsive view

## Deployment Guide

### Frontend Deployment

Recommended:

- Netlify
- Vercel

For Netlify:

1. Push the project to GitHub.
2. Connect GitHub repo to Netlify.
3. Set base directory:

```text
frontend
```

4. Set build command:

```text
npm run build
```

5. Set publish directory:

```text
dist
```

6. Add environment variable:

```env
VITE_API_BASE_URL=https://your-backend-url.onrender.com
```

### Backend Deployment

Recommended low-cost/free options:

- Render
- Railway
- Local demo

For Render:

1. Push project to GitHub.
2. Create a new Web Service.
3. Set root directory:

```text
backend
```

4. Build command:

```text
pip install -r requirements.txt
```

5. Start command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

6. Add environment variables:

```env
GROQ_API_KEY=your_key
LLM_PROVIDER=groq
MODEL_NAME=llama-3.1-8b-instant
CHROMA_DB_PATH=./chroma_db
UPLOAD_DIR=./uploads
FRONTEND_ORIGIN=https://your-frontend-url.netlify.app
```

### Free Deployment Limitations

Free backend services may sleep when inactive. The first request after inactivity may be slow.

Local ChromaDB storage on free hosting may not always persist permanently unless the platform supports persistent disks. For production, consider:

- Hosted vector database
- PostgreSQL with pgvector
- Pinecone
- Weaviate
- Qdrant
- Managed Chroma setup

For a portfolio demo, local ChromaDB is acceptable.

## Future Improvements

- DOCX support
- TXT support
- Website URL ingestion
- OCR for scanned PDFs
- User accounts
- Business workspaces
- Better duplicate document handling
- Advanced source previews
- Streaming responses
- Admin dashboard
- Analytics
- SaaS version for small businesses
- Client-specific knowledge bases
- Customer support widget embed

## Portfolio Positioning

Project title:

```text
AI Knowledge Base Chatbot for Business Support
```

Short description:

```text
A full-stack RAG chatbot that lets businesses upload documents and ask questions using AI. Built with FastAPI, React, ChromaDB, sentence-transformers, and Groq.
```

Business value:

```text
This system helps businesses turn static documents into a searchable AI assistant for customer support, onboarding, training, and faster decision-making.
```

## Built By

**JustCorp Labs**

We build intelligent digital systems for business growth, including websites, dashboards, automation systems, AI tools, and data analytics solutions.