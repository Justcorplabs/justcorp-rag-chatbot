from typing import List, Dict, Any

from groq import Groq

from app.config import settings


SYSTEM_PROMPT = """
You are a helpful business knowledge assistant for JustCorp Labs.

Answer the user's question using only the provided document context.

If the answer is not in the context, say:
"The uploaded documents do not contain enough information to answer that question."

Be clear, concise, and professional.

Do not make up facts.
Do not use outside knowledge.
Do not mention information that is not supported by the provided context.
"""


class LLMClient:
    """
    Handles answer generation using the configured LLM provider.

    Version 1 uses Groq because it is fast and suitable for demos.
    The structure makes it easier to switch to OpenAI, Gemini, or Ollama later.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model_name = settings.MODEL_NAME
        self.groq_api_key = settings.GROQ_API_KEY

        if self.provider == "groq":
            if not self.groq_api_key:
                raise ValueError(
                    "GROQ_API_KEY is missing. Add it to your backend .env file."
                )

            self.client = Groq(api_key=self.groq_api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def build_context_text(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Convert retrieved document chunks into a single context block.
        """

        if not retrieved_chunks:
            return ""

        context_parts = []

        for chunk in retrieved_chunks:
            filename = chunk.get("filename", "Unknown file")
            chunk_number = chunk.get("chunk_number", "Unknown chunk")
            text = chunk.get("text", "")

            context_parts.append(
                f"Source: {filename} | Chunk: {chunk_number}\n{text}"
            )

        return "\n\n---\n\n".join(context_parts)

    def generate_answer(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> str:
        """
        Generate an answer using only retrieved document context.
        """

        context_text = self.build_context_text(retrieved_chunks)

        if not context_text.strip():
            return "The uploaded documents do not contain enough information to answer that question."

        user_prompt = f"""
Document context:
{context_text}

User question:
{question}

Answer using only the document context.
"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT.strip(),
                },
                {
                    "role": "user",
                    "content": user_prompt.strip(),
                },
            ],
            temperature=0.2,
            max_tokens=600,
        )

        answer = response.choices[0].message.content

        if not answer:
            return "The uploaded documents do not contain enough information to answer that question."

        return answer.strip()


llm_client = LLMClient()