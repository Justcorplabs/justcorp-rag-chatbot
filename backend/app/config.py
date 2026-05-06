import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


class Settings:
    """
    Central configuration for the JustCorp Labs AI Knowledge Base backend.
    Values are loaded from environment variables where possible.
    """

    APP_NAME: str = "JustCorp Labs AI Knowledge Base API"
    APP_VERSION: str = "1.0.0"

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # WhatsApp Cloud API settings
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv(
        "WHATSAPP_VERIFY_TOKEN",
        "justcorp_verify_token_123",
    )

    BASE_DIR: Path = Path(__file__).resolve().parent.parent


settings = Settings()