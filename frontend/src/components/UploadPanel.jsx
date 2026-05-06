import { useState } from "react";
import { Upload, Loader2 } from "lucide-react";
import { uploadDocument } from "../api";

function UploadPanel({ onUploaded }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  async function handleUpload(event) {
    event.preventDefault();

    if (!selectedFile) {
      setMessage("Please choose a PDF file first.");
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setMessage("Only PDF files are supported in version 1.");
      return;
    }

    try {
      setUploading(true);
      setMessage("");

      const result = await uploadDocument(selectedFile);

      setMessage(
        `Uploaded successfully: ${result.filename} — ${result.chunks_stored} chunks stored in the knowledge base.`
      );

      setSelectedFile(null);

      if (onUploaded) {
        onUploaded(result);
      }
    } catch (error) {
      setMessage(error.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="card upload-card" id="documents">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Step 1</p>
          <h2>Upload business documents</h2>
        </div>
        <Upload size={22} />
      </div>

      <p className="muted">
        Upload a PDF to build your business knowledge base. The system extracts text,
        creates chunks, generates embeddings, and stores the document for retrieval.
      </p>

      <form onSubmit={handleUpload} className="upload-form">
        <label className="file-input">
          <input
            type="file"
            accept="application/pdf"
            onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
          />
          <span>{selectedFile ? selectedFile.name : "Choose a PDF document"}</span>
        </label>

        <button className="primary-button full-button" type="submit" disabled={uploading}>
          {uploading ? (
            <>
              <Loader2 className="spin" size={18} />
              Processing...
            </>
          ) : (
            "Upload Document"
          )}
        </button>
      </form>

      <p className="muted" style={{ marginTop: "10px", fontSize: "14px" }}>
        Supported in version 1: PDF files
      </p>

      {message && <p className="feedback-message">{message}</p>}
    </section>
  );
}

export default UploadPanel;