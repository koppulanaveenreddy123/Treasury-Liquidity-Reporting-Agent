from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings for the Treasury & Liquidity Reporting Assistant."""

    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "")
        self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
        self.chroma_port = int(os.getenv("CHROMA_PORT", "8001"))
        self.jaeger_endpoint = os.getenv("JAEGER_ENDPOINT", "http://localhost:4318")
        self.prometheus_port = int(os.getenv("PROMETHEUS_PORT", "9090"))
        self.project_root = Path(__file__).resolve().parent.parent
        self.data_dir = Path(os.getenv("DATA_DIR", str(self.project_root / "app" / "data")))
        self.knowledge_dir = Path(os.getenv("KNOWLEDGE_DIR", str(self.project_root / "app" / "knowledge")))
        self.use_mock_llm = os.getenv("USE_MOCK_LLM", "true").lower() == "true"


settings = Settings()
