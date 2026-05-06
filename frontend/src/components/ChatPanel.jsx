import { useState } from "react";
import { Send, Loader2, RotateCcw } from "lucide-react";
import { askQuestion } from "../api";

function ChatPanel({ selectedQuestion, onSourcesUpdate }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Welcome to the JustCorp Labs AI Knowledge Base Chatbot. Upload a document, then ask a question. I will answer using only the uploaded document context.",
    },
  ]);
  const [loading, setLoading] = useState(false);

  function useExampleQuestion() {
    if (selectedQuestion) {
      setQuestion(selectedQuestion);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const cleanQuestion = question.trim();

    if (!cleanQuestion) return;

    const userMessage = {
      role: "user",
      content: cleanQuestion,
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const result = await askQuestion(cleanQuestion, 4);

      const assistantMessage = {
        role: "assistant",
        content: result.answer,
      };

      setMessages((current) => [...current, assistantMessage]);

      if (onSourcesUpdate) {
        onSourcesUpdate(result.sources || []);
      }
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: error.message || "Something went wrong while answering.",
        },
      ]);

      if (onSourcesUpdate) {
        onSourcesUpdate([]);
      }
    } finally {
      setLoading(false);
    }
  }

  function clearChat() {
    setMessages([
      {
        role: "assistant",
        content:
          "Chat cleared. Ask a new question using your uploaded document knowledge base.",
      },
    ]);

    if (onSourcesUpdate) {
      onSourcesUpdate([]);
    }
  }

  return (
    <section className="card chat-card" id="chat">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Step 2</p>
          <h2>Ask your knowledge base</h2>
        </div>

        <button className="icon-button" onClick={clearChat} title="Clear chat">
          <RotateCcw size={18} />
        </button>
      </div>

      <p className="muted" style={{ marginBottom: "16px" }}>
        Ask questions about uploaded business documents. The assistant answers using
        retrieved context from the knowledge base only.
      </p>

      {selectedQuestion && (
        <button className="selected-question" onClick={useExampleQuestion}>
          Use example: {selectedQuestion}
        </button>
      )}

      <div className="chat-window">
        {messages.map((message, index) => (
          <div
            className={`message-row ${
              message.role === "user" ? "user-row" : "assistant-row"
            }`}
            key={`${message.role}-${index}`}
          >
            <div className={`message-bubble ${message.role}`}>
              {message.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-row assistant-row">
            <div className="message-bubble assistant loading-bubble">
              <Loader2 className="spin" size={17} />
              Thinking through the uploaded documents...
            </div>
          </div>
        )}
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about your uploaded documents..."
          rows={3}
        />

        <button className="primary-button send-button" type="submit" disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
          Send
        </button>
      </form>
    </section>
  );
}

export default ChatPanel;