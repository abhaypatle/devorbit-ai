import io
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from pypdf import PdfReader
from pypdf.errors import PdfReadError


@dataclass(frozen=True)
class ParsedSection:
    title: str
    content: str


@dataclass(frozen=True)
class ParsedDocument:
    title: str
    sections: tuple[ParsedSection, ...]


_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")


def parse_document(content: bytes, filename: str, content_type: str) -> ParsedDocument:
    suffix = PurePosixPath(filename.replace("\\", "/")).suffix.lower()
    title = PurePosixPath(filename.replace("\\", "/")).stem or "Untitled document"

    if suffix == ".pdf" or content_type == "application/pdf":
        try:
            pages = [page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages]
        except (PdfReadError, ValueError, OSError) as exc:
            raise ValueError("The uploaded PDF could not be parsed") from exc
        text = "\n\n".join(pages).strip()
        if not text:
            raise ValueError("The uploaded PDF contains no extractable text")
        return ParsedDocument(
            title=title,
            sections=tuple(ParsedSection(f"Page {index + 1}", page) for index, page in enumerate(pages) if page.strip()),
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Document must contain UTF-8 text or be a readable PDF") from exc

    if suffix == ".json" or content_type == "application/json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("Uploaded JSON document is invalid") from exc
        text = json.dumps(parsed, ensure_ascii=False, indent=2)
        return ParsedDocument(title=title, sections=(ParsedSection("JSON document", text),))

    if suffix not in {".md", ".markdown", ".txt"} and not content_type.startswith("text/"):
        raise ValueError("Supported document types are Markdown, text, JSON, and text-based PDF")

    sections: list[ParsedSection] = []
    current_title = title
    current_lines: list[str] = []
    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading:
            current_content = "\n".join(current_lines).strip()
            if current_content:
                sections.append(ParsedSection(current_title, current_content))
            current_title = heading.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
    remaining = "\n".join(current_lines).strip()
    if remaining:
        sections.append(ParsedSection(current_title, remaining))
    if not sections and text.strip():
        sections.append(ParsedSection(title, text.strip()))
    if not sections:
        raise ValueError("Uploaded document is empty")
    return ParsedDocument(title=title, sections=tuple(sections))
