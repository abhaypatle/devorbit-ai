import math
import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from app.db.models import DocumentChunk, ProjectDocument
from app.rag.chunker import DocumentChunkData


@dataclass(frozen=True)
class ScoredChunk:
    chunk: DocumentChunk
    score: float


async def store_chunks(
    session: AsyncSession,
    chunks: list[DocumentChunkData],
    embeddings: list[list[float]],
) -> list[DocumentChunk]:
    if len(chunks) != len(embeddings):
        raise ValueError("Every document chunk must have exactly one embedding")
    records = [
        DocumentChunk(
            org_id=chunk.org_id,
            project_id=chunk.project_id,
            doc_id=chunk.doc_id,
            doc_title=chunk.doc_title,
            section=chunk.section,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            embedding=embedding,
        )
        for chunk, embedding in zip(chunks, embeddings, strict=True)
    ]
    session.add_all(records)
    return records


async def search_chunks(
    session: AsyncSession,
    *,
    org_id: UUID,
    project_id: UUID,
    query_embedding: list[float],
    query_text: str,
    top_k: int,
    approved_only: bool = False,
) -> list[ScoredChunk]:
    base = (
        select(DocumentChunk)
        .join(
            ProjectDocument,
            (ProjectDocument.id == DocumentChunk.doc_id)
            & (ProjectDocument.org_id == DocumentChunk.org_id)
            & (ProjectDocument.project_id == DocumentChunk.project_id),
        )
        .where(
            DocumentChunk.org_id == org_id,
            DocumentChunk.project_id == project_id,
            ProjectDocument.org_id == org_id,
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "indexed",
        )
    )
    if approved_only:
        base = base.where(ProjectDocument.is_approved.is_(True))
    bind = session.get_bind()
    if bind.dialect.name == "postgresql":
        distance = DocumentChunk.embedding.op("<=>")(
            literal(query_embedding, type_=Vector(len(query_embedding)))
        )
        vector_rows = (
            await session.execute(base.order_by(distance).limit(top_k * 3))
        ).all()
        candidates = {row[0].id: row[0] for row in vector_rows}
        lexical_terms = sorted(_terms(query_text))
        if lexical_terms:
            predicates = [
                DocumentChunk.content.ilike(f"%{term}%", escape="\\")
                for term in lexical_terms[:12]
            ]
            lexical_rows = await session.scalars(
                base.where(or_(*predicates)).limit(top_k * 3)
            )
            candidates.update({chunk.id: chunk for chunk in lexical_rows})
    else:
        candidates = {
            chunk.id: chunk for chunk in (await session.scalars(base)).all()
        }

    scored = [
        ScoredChunk(
            chunk=chunk,
            score=_hybrid_score(query_text, query_embedding, chunk),
        )
        for chunk in candidates.values()
    ]
    return sorted(scored, key=lambda result: result.score, reverse=True)[:top_k]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Query and stored embeddings have different dimensions")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)


def _terms(text: str) -> set[str]:
    return {term.casefold() for term in re.findall(r"[a-z0-9]+", text, re.I) if len(term) > 2}


def _hybrid_score(query: str, query_embedding: list[float], chunk: DocumentChunk) -> float:
    vector_score = (_cosine_similarity(query_embedding, chunk.embedding) + 1.0) / 2.0
    query_terms = _terms(query)
    if not query_terms:
        return vector_score
    lexical_score = len(query_terms & _terms(chunk.content)) / len(query_terms)
    return 0.7 * vector_score + 0.3 * lexical_score
