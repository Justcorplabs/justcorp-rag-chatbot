import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.document_loader import extract_text_from_pdf, clean_extracted_text
from app.chunker import split_text_into_chunks
from app.embeddings import embedding_model
from app.vector_store import vector_store
from app.rag_pipeline import rag_pipeline
from app.llm_client import llm_client
from app.whatsapp_webhook import router as whatsapp_router
from app.models import (
    DocumentUploadResponse,
    DocumentsListResponse,
    DeleteDocumentResponse,
    SearchRequest,
    SearchResponse,
    AskRequest,
    AskResponse,
    TestAnswerRequest,
    TestAnswerResponse,
)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for the JustCorp Labs AI Knowledge Base Chatbot.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_ORIGIN,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(whatsapp_router)


UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def build_sources(retrieved_chunks):
    """
    Convert retrieved chunks into clean source objects for API responses.
    """

    sources = []

    for chunk in retrieved_chunks:
        sources.append(
            {
                "document_id": chunk["document_id"],
                "filename": chunk["filename"],
                "chunk_number": chunk["chunk_number"],
                "distance": chunk["distance"],
            }
        )

    return sources


@app.get("/")
def root():
    return {
        "message": "Welcome to the JustCorp Labs AI Knowledge Base API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "JustCorp Labs AI Knowledge Base API is running",
        "version": settings.APP_VERSION,
    }


@app.post("/upload-document", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF document, extract text, split into chunks,
    generate embeddings, and store chunks in ChromaDB.
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    original_filename = file.filename
    file_extension = Path(original_filename).suffix.lower()

    if file_extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported in version 1.",
        )

    document_id = str(uuid.uuid4())

    safe_filename = original_filename.replace(" ", "_")
    saved_filename = f"{document_id}_{safe_filename}"
    saved_path = UPLOAD_DIR / saved_filename

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        raw_text = extract_text_from_pdf(str(saved_path))
        cleaned_text = clean_extracted_text(raw_text)

        if not cleaned_text:
            raise HTTPException(
                status_code=400,
                detail="The PDF was uploaded, but no readable text could be extracted.",
            )

        chunks = split_text_into_chunks(
            text=cleaned_text,
            document_id=document_id,
            filename=original_filename,
            chunk_size=900,
            overlap=150,
        )

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="The PDF text was extracted, but no chunks could be created.",
            )

        chunk_texts = [chunk["text"] for chunk in chunks]

        embeddings = embedding_model.embed_texts(chunk_texts)

        if not embeddings:
            raise HTTPException(
                status_code=500,
                detail="Chunks were created, but embeddings could not be generated.",
            )

        chunks_stored = vector_store.add_document_chunks(
            chunks=chunks,
            embeddings=embeddings,
        )

        embedding_dimension = len(embeddings[0])

        sample_embedding_preview = [
            round(value, 4) for value in embeddings[0][:5]
        ] + ["..."]

        preview_chunks = chunks[:3]

        return DocumentUploadResponse(
            document_id=document_id,
            filename=original_filename,
            file_path=str(saved_path),
            text_length=len(cleaned_text),
            chunks_created=len(chunks),
            chunks_stored=chunks_stored,
            embedding_dimension=embedding_dimension,
            sample_embedding_preview=sample_embedding_preview,
            chunks_preview=preview_chunks,
            message="Document uploaded, text extracted, chunks created, embeddings generated, and stored in ChromaDB successfully.",
        )

    except HTTPException:
        raise

    except Exception as error:
        if saved_path.exists():
            saved_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process uploaded document: {str(error)}",
        )

    finally:
        await file.close()


@app.get("/documents", response_model=DocumentsListResponse)
def get_documents():
    """
    List all uploaded documents currently stored in ChromaDB.
    """

    documents = vector_store.list_documents()

    return DocumentsListResponse(documents=documents)


@app.delete("/documents/{document_id}", response_model=DeleteDocumentResponse)
def delete_document(document_id: str):
    """
    Delete a document's chunks from ChromaDB.
    """

    chunks_deleted = vector_store.delete_document(document_id=document_id)

    if chunks_deleted == 0:
        raise HTTPException(
            status_code=404,
            detail="Document not found in ChromaDB.",
        )

    return DeleteDocumentResponse(
        document_id=document_id,
        chunks_deleted=chunks_deleted,
        message="Document deleted successfully from ChromaDB.",
    )


@app.post("/search", response_model=SearchResponse)
def search_documents(request: SearchRequest):
    """
    Search uploaded documents and return the most relevant chunks.
    This tests the retrieval part of RAG before connecting the LLM.
    """

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    results = rag_pipeline.retrieve_context(
        question=question,
        top_k=request.top_k,
    )

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No relevant document chunks found. Upload a document first.",
        )

    return SearchResponse(
        question=question,
        results=results,
    )


@app.post("/test-answer", response_model=TestAnswerResponse)
def test_answer_generation(request: TestAnswerRequest):
    """
    Debug endpoint for Groq answer generation.
    The production chatbot endpoint is /ask.
    """

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    retrieved_chunks = rag_pipeline.retrieve_context(
        question=question,
        top_k=request.top_k,
    )

    if not retrieved_chunks:
        raise HTTPException(
            status_code=404,
            detail="No relevant document chunks found. Upload a document first.",
        )

    answer = llm_client.generate_answer(
        question=question,
        retrieved_chunks=retrieved_chunks,
    )

    return TestAnswerResponse(
        question=question,
        answer=answer,
        sources=build_sources(retrieved_chunks),
    )


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    """
    Main production RAG chatbot endpoint.

    Flow:
    - receive user question
    - retrieve relevant document chunks from ChromaDB
    - generate answer with Groq using only retrieved context
    - return answer and sources
    """

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    retrieved_chunks = rag_pipeline.retrieve_context(
        question=question,
        top_k=request.top_k,
    )

    if not retrieved_chunks:
        return AskResponse(
            question=question,
            answer="The uploaded documents do not contain enough information to answer that question.",
            sources=[],
        )

    answer = llm_client.generate_answer(
        question=question,
        retrieved_chunks=retrieved_chunks,
    )

    sources = build_sources(retrieved_chunks)

    return AskResponse(
        question=question,
        answer=answer,
        sources=sources,
    )