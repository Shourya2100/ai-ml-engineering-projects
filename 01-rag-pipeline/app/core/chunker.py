import tiktoken

from common.logging import get_logger

logger = get_logger(__name__)

_encoder = tiktoken.get_encoding("cl100k_base")


def chunk_document(
    text: str,
    filename: str,
    chunk_size: int = 400,
    overlap: int = 50,
) -> list[dict]:
    """Split a document into overlapping chunks of fixed token size.

    Each chunk carries metadata: text, filename, section heading, chunk index, and
    a stable chunk_id suitable for targeted deletion.
    """
    if not text.strip():
        return []

    lines = text.split("\n")
    current_section = "General"
    line_sections: list[tuple[str, str]] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            current_section = stripped.lstrip("# ").strip()
        line_sections.append((line, current_section))

    tokens = _encoder.encode(text)

    if len(tokens) <= chunk_size:
        return [
            {
                "text": text.strip(),
                "filename": filename,
                "section": current_section,
                "chunk_index": 0,
                "chunk_id": f"{filename}__chunk_0",
            }
        ]

    # Build a mapping from token index to section heading.
    # Walk through the document line by line, tracking which section each token belongs to.
    char_offset = 0
    token_sections: list[str] = ["General"] * len(tokens)
    for line, section in line_sections:
        line_with_newline = line + "\n"
        line_tokens = _encoder.encode(line_with_newline)
        for _ in line_tokens:
            if char_offset < len(tokens):
                token_sections[char_offset] = section
                char_offset += 1

    chunks: list[dict] = []
    start = 0
    chunk_index = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = _encoder.decode(chunk_tokens).strip()

        section = token_sections[start]

        chunks.append(
            {
                "text": chunk_text,
                "filename": filename,
                "section": section,
                "chunk_index": chunk_index,
                "chunk_id": f"{filename}__chunk_{chunk_index}",
            }
        )

        chunk_index += 1
        start += chunk_size - overlap

        if start >= len(tokens):
            break

    logger.info("Chunked '%s' into %d chunks", filename, len(chunks))
    return chunks
