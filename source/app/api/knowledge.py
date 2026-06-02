"""Knowledge Base API"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from loguru import logger

from app.api.schemas import KnowledgeItem
from app.llm.rag import rag_kb

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.get("/search", response_model=List[KnowledgeItem])
async def search_knowledge(
    query: str = Query(..., description="Search keyword"),
    category: Optional[str] = Query(None, description="Knowledge category"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results to return")
):
    """Search the anti-fraud knowledge base"""
    try:
        results = await rag_kb.search_knowledge(
            query=query,
            top_k=top_k,
            category=category
        )

        return [
            KnowledgeItem(
                id=i,
                title=result["title"],
                content=result["content"],
                category=result["category"],
                tags=result["tags"],
                source=result.get("source", "")
            )
            for i, result in enumerate(results)
        ]
    except Exception as e:
        logger.error(f"Knowledge base search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/categories", response_model=List[str])
async def get_categories():
    """Get all knowledge base categories"""
    categories = set()
    for item in rag_kb.knowledge_data:
        if item.get("category"):
            categories.add(item["category"])
    return list(categories)


@router.get("/prevention-guide", response_model=str)
async def get_prevention_guide(topic: Optional[str] = None):
    """Get fraud prevention guide"""
    try:
        if topic:
            results = await rag_kb.search_knowledge(
                query=topic,
                top_k=1,
                category="prevention_guide"
            )
        else:
            results = await rag_kb.search_knowledge(
                query="fraud prevention guide",
                top_k=1,
                category="prevention_guide"
            )

        if results:
            return results[0]["content"]
        else:
            return "No relevant fraud prevention guide available"
    except Exception as e:
        logger.error(f"Failed to get prevention guide: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get guide: {str(e)}")


@router.get("/fraud-cases", response_model=List[KnowledgeItem])
async def get_fraud_cases(category: Optional[str] = None):
    """Get fraud case examples"""
    try:
        results = await rag_kb.search_knowledge(
            query="fraud cases",
            top_k=10,
            category="fraud_case"
        )

        if category:
            results = [r for r in results if category in r.get("tags", [])]

        return [
            KnowledgeItem(
                id=i,
                title=result["title"],
                content=result["content"],
                category=result["category"],
                tags=result["tags"],
                source=result.get("source", "")
            )
            for i, result in enumerate(results)
        ]
    except Exception as e:
        logger.error(f"Failed to get fraud cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cases: {str(e)}")
