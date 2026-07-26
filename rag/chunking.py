"""Markdown-aware document chunking.

Strategy: split on markdown headings (##/###) so each chunk is one
self-contained README section, then sub-split any section longer than
MAX_WORDS at paragraph boundaries with a small overlap.

Why header-based rather than fixed-size token windows:
- READMEs are deliberately structured documents. A section like
  "## Data Warehousing (BigQuery)" is a coherent unit of meaning; a fixed
  256-token window would routinely cut a table or a result figure away
  from the sentence that explains it, which directly hurts answer
  grounding ("58.7%" without "bytes scanned" next to it is useless).
- Headings double as citation metadata for free — every chunk knows the
  project and section it came from, so answers can cite
  "uk-retail-data-platform > Data Warehousing (BigQuery)".
- The corpus is small (a handful of READMEs), so we don't need the
  uniformity fixed-size windows give large corpora for batching/ANN.

The fallback sub-split exists because some sections run long (the crime
README's Kafka section is ~600 words); embedding models degrade past
their effective context, and over-long chunks dilute similarity scores.
Sub-splits break at paragraph boundaries (never inside a code fence) and
carry PARA_OVERLAP paragraphs of overlap so a fact stated at a boundary
appears in both pieces.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

MAX_WORDS = 350
PARA_OVERLAP = 1  # paragraphs of overlap between sub-splits of a long section


@dataclass
class Chunk:
    text: str
    project: str
    source_file: str
    heading: str
    chunk_id: str = field(default="")

    def citation(self) -> str:
        return f"{self.project} > {self.heading}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Chunk":
        return cls(**d)


def _split_paragraphs(text: str) -> list[str]:
    """Split on blank lines, but never inside a fenced code block."""
    paragraphs: list[str] = []
    current: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if line.strip() == "" and not in_fence:
            if current:
                paragraphs.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append("\n".join(current))
    return paragraphs


def _word_count(text: str) -> int:
    return len(text.split())


def _sub_split(paragraphs: list[str]) -> list[str]:
    """Greedily pack paragraphs into pieces of at most MAX_WORDS,
    overlapping PARA_OVERLAP paragraphs between consecutive pieces."""
    pieces: list[str] = []
    i = 0
    while i < len(paragraphs):
        words = 0
        j = i
        while j < len(paragraphs) and (words == 0 or words + _word_count(paragraphs[j]) <= MAX_WORDS):
            words += _word_count(paragraphs[j])
            j += 1
        pieces.append("\n\n".join(paragraphs[i:j]))
        if j >= len(paragraphs):
            break
        i = max(j - PARA_OVERLAP, i + 1)
    return pieces


def split_sections(markdown: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) sections on ## / ### headings.

    Content before the first heading becomes an 'Introduction' section
    titled with the document's H1 if present. Heading markers inside
    code fences are ignored.
    """
    lines = markdown.splitlines()
    sections: list[tuple[str, list[str]]] = []
    title = "Introduction"
    current_heading = title
    current_lines: list[str] = []
    in_fence = False

    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        m = re.match(r"^(#{1,3})\s+(.*)$", line) if not in_fence else None
        if m:
            level, heading_text = len(m.group(1)), m.group(2).strip()
            if level == 1:
                title = heading_text
                if current_heading == "Introduction":
                    current_heading = f"{heading_text} (Introduction)"
                continue
            sections.append((current_heading, current_lines))
            current_heading = heading_text
            current_lines = []
        else:
            current_lines.append(line)
    sections.append((current_heading, current_lines))

    out = []
    for heading, body_lines in sections:
        body = "\n".join(body_lines).strip()
        # drop separator-only or empty sections
        if not body or re.fullmatch(r"[-\s]*", body):
            continue
        out.append((heading, body))
    return out


def chunk_markdown(markdown: str, project: str, source_file: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    for heading, body in split_sections(markdown):
        paragraphs = _split_paragraphs(body)
        if _word_count(body) <= MAX_WORDS:
            pieces = ["\n\n".join(paragraphs)]
        else:
            pieces = _sub_split(paragraphs)
        for idx, piece in enumerate(pieces):
            suffix = f" (part {idx + 1})" if len(pieces) > 1 else ""
            chunk = Chunk(
                text=piece,
                project=project,
                source_file=source_file,
                heading=heading + suffix,
            )
            chunk.chunk_id = f"{project}::{heading}::{idx}"
            chunks.append(chunk)
    return chunks


def load_and_chunk(doc_paths: list[Path]) -> list[Chunk]:
    """Read one or more markdown files; the file stem is the project name."""
    all_chunks: list[Chunk] = []
    for path in doc_paths:
        text = path.read_text(encoding="utf-8")
        all_chunks.extend(chunk_markdown(text, project=path.stem, source_file=path.name))
    return all_chunks
