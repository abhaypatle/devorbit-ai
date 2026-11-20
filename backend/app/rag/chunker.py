from dataclasses import dataclass
from uuid import UUID

from app.core.config import get_settings
from app.rag.parser import ParsedDocument


@dataclass(frozen=True)
class DocumentChunkData:
    org_id: UUID
    project_id: UUID
    doc_id: UUID
    doc_title: str
    section: str | None
    chunk_index: int
    content: str


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Chunk overlap must be non-negative and smaller than chunk size")
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = max(text.rfind("\n", start, end), text.rfind(" ", start, end))
            if boundary > start + chunk_size // 2:
                end = boundary
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def chunk_document(
    parsed: ParsedDocument,
    *,
    org_id: UUID,
    project_id: UUID,
    doc_id: UUID,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[DocumentChunkData]:
    settings = get_settings()
    size = chunk_size if chunk_size is not None else settings.rag_chunk_size
    chunk_overlap = overlap if overlap is not None else settings.rag_chunk_overlap
    chunks: list[DocumentChunkData] = []
    for section in parsed.sections:
        for content in _split_text(section.content, size, chunk_overlap):
            chunks.append(
                DocumentChunkData(
                    org_id=org_id,
                    project_id=project_id,
                    doc_id=doc_id,
                    doc_title=parsed.title,
                    section=section.title,
                    chunk_index=len(chunks),
                    content=content,
                )
            )
    return chunks
