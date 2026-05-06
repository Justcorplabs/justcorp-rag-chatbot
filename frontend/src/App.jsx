import { useEffect, useState } from "react";
import Header from "./components/Header";
import UploadPanel from "./components/UploadPanel";
import DocumentList from "./components/DocumentList";
import ExampleQuestions from "./components/ExampleQuestions";
import ChatPanel from "./components/ChatPanel";
import SourcePanel from "./components/SourcePanel";
import { checkHealth, getDocuments } from "./api";
import "./styles.css";

function App() {
  const [apiStatus, setApiStatus] = useState("offline");
  const [documents, setDocuments] = useState([]);
  const [selectedQuestion, setSelectedQuestion] = useState("");
  const [sources, setSources] = useState([]);

  async function loadDocuments() {
    try {
      const result = await getDocuments();
      setDocuments(result.documents || []);
    } catch (error) {
      console.error("Failed to load documents:", error);
      setDocuments([]);
    }
  }

  async function checkApiStatus() {
    try {
      await checkHealth();
      setApiStatus("online");
    } catch (error) {
      setApiStatus("offline");
    }
  }

  useEffect(() => {
    checkApiStatus();
    loadDocuments();
  }, []);

  async function handleUploadComplete() {
    await loadDocuments();
  }

  return (
    <div className="app-shell">
      <Header apiStatus={apiStatus} />

      <main className="main-layout">
        <div className="left-column">
          <UploadPanel onUploaded={handleUploadComplete} />
          <DocumentList documents={documents} onRefresh={loadDocuments} />
          <ExampleQuestions onSelectQuestion={setSelectedQuestion} />
        </div>

        <div className="right-column">
          <ChatPanel
            selectedQuestion={selectedQuestion}
            onSourcesUpdate={setSources}
          />
          <SourcePanel sources={sources} />
        </div>
      </main>

      <footer className="footer">
        <p>
          Built by <strong>JustCorp Labs</strong> — intelligent digital systems for
          business growth.
        </p>
      </footer>
    </div>
  );
}

export default App;