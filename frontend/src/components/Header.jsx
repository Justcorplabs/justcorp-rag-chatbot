import { Brain, Database, FileSearch } from "lucide-react";

function Header({ apiStatus }) {
  return (
    <header className="hero">
      <nav className="top-nav">
        <div className="brand">
          <img
            src="/justcorp-logo.jpeg"
            alt="JustCorp Labs logo"
            className="brand-logo"
          />

          <div>
            <p className="brand-name">JustCorp Labs</p>
            <p className="brand-subtitle">AI Knowledge Base Chatbot</p>
          </div>
        </div>

        <div className={`status-pill ${apiStatus === "online" ? "online" : "offline"}`}>
          <span className="status-dot" />
          {apiStatus === "online" ? "API Online" : "API Offline"}
        </div>
      </nav>

      <div className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">Business AI Assistant</p>
          <h1>Turn company documents into a searchable AI knowledge base.</h1>
          <p className="hero-text">
            We build intelligent digital systems for business growth. This AI assistant
            transforms business documents into a searchable knowledge base for customer
            support, onboarding, internal training, and faster decision-making.
          </p>

          <div className="hero-actions">
            <a href="#chat" className="primary-button">
              Ask a Question
            </a>
            <a href="#documents" className="secondary-button">
              Upload Documents
            </a>
          </div>
        </div>

        <div className="hero-card">
          <div className="mini-card">
            <FileSearch size={22} />
            <div>
              <strong>Document Ingestion</strong>
              <span>Upload PDFs and convert them into clean searchable text.</span>
            </div>
          </div>

          <div className="mini-card">
            <Database size={22} />
            <div>
              <strong>Semantic Search</strong>
              <span>Retrieve relevant context from your document knowledge base.</span>
            </div>
          </div>

          <div className="mini-card">
            <Brain size={22} />
            <div>
              <strong>Grounded Answers</strong>
              <span>Generate answers using uploaded document context only.</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;