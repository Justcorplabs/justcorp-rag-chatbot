const exampleQuestions = [
  "What is this document about?",
  "Summarize the key points from the uploaded document.",
  "Which models were evaluated in the study?",
  "What problem does the document address?",
  "What are the main findings in the document?",
  "What services does JustCorp Labs offer?",
];

function ExampleQuestions({ onSelectQuestion }) {
  return (
    <section className="card compact-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Try asking</p>
          <h2>Example questions</h2>
        </div>
      </div>

      <p className="muted" style={{ marginBottom: "16px" }}>
        Use these examples to quickly test the knowledge base assistant.
      </p>

      <div className="question-chips">
        {exampleQuestions.map((question) => (
          <button
            key={question}
            className="question-chip"
            onClick={() => onSelectQuestion(question)}
          >
            {question}
          </button>
        ))}
      </div>
    </section>
  );
}

export default ExampleQuestions;