from __future__ import annotations

import json
from pathlib import Path

from app.agent.mock_llm_provider import MockLLMProvider
from app.agent.orchestrator import Orchestrator
from app.tools.knowledge_retriever import KnowledgeRetriever


def main() -> None:
    """Run a lightweight demo of the system using synthetic inputs and guidance."""
    metrics = {"net_cash_available": 2450000.0, "lcr_ratio": 1.5}
    guidance = KnowledgeRetriever(knowledge_dir="app/knowledge").load_guidance("liquidity")
    narrative = Orchestrator(llm_provider=MockLLMProvider()).generate_narrative(metrics, guidance, "healthy")
    print(json.dumps({"metrics": metrics, "guidance_count": len(guidance), "narrative": narrative}, indent=2))


if __name__ == "__main__":
    main()
