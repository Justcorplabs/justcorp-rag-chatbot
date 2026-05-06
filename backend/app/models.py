from pydantic import BaseModel
from typing import List, Optional, Union


class DocumentChunk(BaseModel):
    document_id: str
    filename: str
    chunk_number: int
    text: str


class DocumentSummary(BaseModel):
    document_id: str
    filename: str
    chunks: int


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_path: str
    text_length: int
    chunks_created: int
    chunks_stored: int
    embedding_dimension: int
    sample_embedding_preview: List[Union[float, str]]
    chunks_preview: List[DocumentChunk]
    message: str


class DocumentsListResponse(BaseModel):
    documents: List[DocumentSummary]


class DeleteDocumentResponse(BaseModel):
    document_id: str
    chunks_deleted: int
    message: str


class SearchRequest(BaseModel):
    question: str
    top_k: int = 4


class SearchResult(BaseModel):
    document_id: str
    filename: str
    chunk_number: int
    text: str
    distance: float


class SearchResponse(BaseModel):
    question: str
    results: List[SearchResult]


class SourceUsed(BaseModel):
    document_id: str
    filename: str
    chunk_number: int
    distance: float


class AskRequest(BaseModel):
    question: str
    top_k: int = 4


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceUsed]


class TestAnswerRequest(BaseModel):
    question: str
    top_k: int = 4


class TestAnswerResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceUsed]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None