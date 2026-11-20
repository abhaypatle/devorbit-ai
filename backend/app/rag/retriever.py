from dataclasses import asdict, dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.rag.embedder import get_embedder
from app.rag.pgvector_store import search_chunks


@dataclass(frozen=True)
class Citation:
    doc_id: str
    doc_title: str
    chunk_index: int
    snippet: str
    section: str | None
    score: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RetrievalResult:
    citations: tuple[Citation, ...]
    context: str


async def retrieve(
    session: AsyncSession,
    *,
    org_id: UUID,
    project_id: UUID,
    query: str,
    top_k: int | None = None,
    approved_only: bool = False,
) -> RetrievalResult:
    embedding = (await get_embedder().embed([query]))[0]
    matches = await search_chunks(
        session,
        org_id=org_id,
        project_id=project_id,
        query_embedding=embedding,
        query_text=query,
        top_k=top_k or get_settings().rag_top_k,
        approved_only=approved_only,
    )
    citations = tuple(
        Citation(
            doc_id=str(match.chunk.doc_id),
            doc_title=match.chunk.doc_title,
            chunk_index=match.chunk.chunk_index,
            snippet=match.chunk.content[:500],
            section=match.chunk.section,
            score=round(match.score, 6),
        )
        for match in matches
    )
    context = "\n\n".join(
        f"[{citation.doc_title} | section: {citation.section or 'General'} | "
        f"chunk: {citation.chunk_index}]\n{citation.snippet}"
        for citation in citations
    )
    return RetrievalResult(citations=citations, context=context)
