"""
Text Chunking Helper.

Implements Recursive Character Text Splitting with Sliding Window Overlap.
Preserves paragraph, sentence, and phrase integrity while respecting strict token/char boundaries.
"""
from typing import List


def recursive_chunk_text(
    text: str,
    chunk_size: int = 600,
    chunk_overlap: int = 100,
) -> List[str]:
    """
    Recursively splits raw text into smaller overlapping chunks.

    Separators tried in order of priority:
    1. Paragraph break ("\\n\\n")
    2. Line break ("\\n")
    3. Sentence boundary (". ")
    4. Word boundary (" ")

    :param text: Input raw text string.
    :param chunk_size: Target maximum characters per chunk.
    :param chunk_overlap: Character overlap between consecutive chunks.
    :return: List of clean text chunk strings.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    separators = ["\n\n", "\n", ". ", " "]

    def _split_recursive(content: str, sep_index: int) -> List[str]:
        if len(content) <= chunk_size or sep_index >= len(separators):
            return [content] if content.strip() else []

        sep = separators[sep_index]
        splits = content.split(sep)
        chunks: List[str] = []
        current_chunk = ""

        for part in splits:
            candidate = f"{current_chunk}{sep}{part}" if current_chunk else part
            if len(candidate) <= chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # If a single part is larger than chunk_size, recurse on next separator
                if len(part) > chunk_size:
                    chunks.extend(_split_recursive(part, sep_index + 1))
                    current_chunk = ""
                else:
                    current_chunk = part

        if current_chunk and current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    raw_chunks = _split_recursive(text, 0)

    # Apply sliding window overlap across chunks to preserve context continuity
    if chunk_overlap <= 0 or len(raw_chunks) <= 1:
        return raw_chunks

    overlapped_chunks: List[str] = []
    for i, chunk in enumerate(raw_chunks):
        if i == 0:
            overlapped_chunks.append(chunk)
        else:
            prev_chunk = raw_chunks[i - 1]
            overlap_prefix = prev_chunk[-chunk_overlap:].strip()
            # Avoid duplicate joins if overlap begins mid-word
            merged = f"...{overlap_prefix} {chunk}" if overlap_prefix else chunk
            overlapped_chunks.append(merged)

    return overlapped_chunks

