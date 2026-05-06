import { FileText, Trash2, RefreshCw } from "lucide-react";
import { deleteDocument } from "../api";

function DocumentList({ documents, onRefresh }) {
  async function handleDelete(documentId) {
    const confirmDelete = window.confirm(
      "Delete this document from the knowledge base?"
    );

    if (!confirmDelete) return;

    try {
      await deleteDocument(documentId);

      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      alert(error.message || "Failed to delete document.");
    }
  }

  return (
    <section className="card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Knowledge Base</p>
          <h2>Uploaded documents</h2>
        </div>

        <button className="icon-button" onClick={onRefresh} title="Refresh documents">
          <RefreshCw size={18} />
        </button>
      </div>

      <p className="muted" style={{ marginBottom: "16px" }}>
        These are the documents currently indexed and searchable by the assistant.
      </p>

      {documents.length === 0 ? (
        <div className="empty-state">
          <FileText size={28} />
          <p>No documents uploaded yet.</p>
          <span>Upload a PDF to start building the JustCorp Labs AI knowledge base.</span>
        </div>
      ) : (
        <div className="document-list">
          {documents.map((document) => (
            <div className="document-item" key={document.document_id}>
              <div className="document-icon">
                <FileText size={20} />
              </div>

              <div className="document-info">
                <strong>{document.filename}</strong>
                <span>{document.chunks} chunks indexed</span>
              </div>

              <button
                className="delete-button"
                onClick={() => handleDelete(document.document_id)}
                title="Delete document"
              >
                <Trash2 size={17} />
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default DocumentList;