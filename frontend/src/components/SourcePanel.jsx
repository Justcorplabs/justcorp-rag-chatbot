import { Link2 } from "lucide-react";

function SourcePanel({ sources }) {
  if (!sources || sources.length === 0) {
    return (
      <section className="card source-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Sources</p>
            <h2>Context used</h2>
          </div>
        </div>

        <p className="muted">
          Source references will appear here after the assistant answers a question.
        </p>
      </section>
    );
  }

  return (
    <section className="card source-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Sources</p>
          <h2>Context used</h2>
        </div>
        <Link2 size={20} />
      </div>

      <p className="muted" style={{ marginBottom: "16px" }}>
        These document chunks were retrieved and used to generate the answer.
      </p>

      <div className="source-list">
        {sources.map((source, index) => (
          <div
            className="source-item"
            key={`${source.document_id}-${source.chunk_number}-${index}`}
          >
            <strong>{source.filename}</strong>
            <span>Chunk {source.chunk_number}</span>
            <small>Distance: {Number(source.distance).toFixed(4)}</small>
          </div>
        ))}
      </div>
    </section>
  );
}

export default SourcePanel;