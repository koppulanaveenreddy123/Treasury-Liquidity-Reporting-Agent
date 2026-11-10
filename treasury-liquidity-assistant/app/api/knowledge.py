from __future__ import annotations

from fastapi import APIRouter

from app.tools.knowledge_retriever import KnowledgeRetriever

router = APIRouter(prefix="/api/v1", tags=["knowledge"])


@router.post("/knowledge/ingest")
async def ingest_knowledge() -> dict:
    retriever = KnowledgeRetriever()
    return {"documents": retriever.ingest()}


@router.post("/knowledge/search")
async def search_knowledge(payload: dict) -> dict:
    query = payload.get("query", "Treasury guidance")
    limit = int(payload.get("limit", 5))
    retriever = KnowledgeRetriever()
    return {"results": retriever.search(query, limit=limit)}
