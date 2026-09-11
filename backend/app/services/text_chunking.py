"""Paragraph/sentence-aware chunking for retrieval-friendly document ingestion."""

from __future__ import annotations

import re

DEFAULT_MAX_CHARS = 1200
DEFAULT_OVERLAP_CHARS = 150
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, max_chars: int = DEFAULT_MAX_CHARS, overlap_chars: int = DEFAULT_OVERLAP_CHARS) -> list[str]:
    normalized = _normalize(text)
    if not normalized:
        return []
    max_chars = max(1, int(max_chars))
    overlap_chars = max(0, min(int(overlap_chars), max_chars // 2))
    if len(normalized) <= max_chars:
        return [normalized]
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
    units: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            units.append(paragraph)
            continue
        sentences = [s.strip() for s in _SENTENCE_BOUNDARY.split(paragraph) if s.strip()] or [paragraph]
        for sentence in sentences:
            if len(sentence) <= max_chars:
                units.append(sentence)
            else:
                units.extend(sentence[i:i + max_chars].strip() for i in range(0, len(sentence), max_chars) if sentence[i:i + max_chars].strip())
    chunks: list[str] = []
    current = ""
    for unit in units:
        candidate = f"{current}\n\n{unit}" if current else unit
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = unit
    if current:
        chunks.append(current.strip())
    if overlap_chars and len(chunks) > 1:
        result = [chunks[0]]
        for previous, current in zip(chunks, chunks[1:]):
            overlap = previous[-overlap_chars:].strip()
            if overlap and not current.startswith(overlap):
                current = f"{overlap} {current}"[:max_chars].strip()
            result.append(current)
        chunks = result
    return chunks


def _normalize(text: str) -> str:
    lines = [(line or "").strip() for line in (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    output: list[str] = []
    last_blank = False
    for line in lines:
        if line:
            output.append(line)
            last_blank = False
        elif not last_blank:
            output.append("")
            last_blank = True
    return "\n".join(output).strip()
