"""Turkish-aware sentence chunking for long-form narration."""
import re
from dataclasses import dataclass

from . import config
from .turkish_normalizer import normalize_turkish

# Abbreviations that end with a period but do not end a sentence (lowercase match).
_ABBREVIATIONS = {
    "hz", "dr", "prof", "doç", "av", "sn", "bkz", "vb", "vs", "örn", "yy",
    "s.a.v", "a.s", "r.a", "s.a", "c.c", "no", "st", "mah", "cad", "sok",
}
_SENTENCE_END = re.compile(r"([.!?…]+[\"'”’»)]*)\s+")
_SOFT_BREAK = re.compile(r"(?<=[,;:])\s+")


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Paragraph breaks are sentence boundaries even without punctuation.
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    return "\n".join(p for p in paragraphs if p)


def _is_false_boundary(before: str) -> bool:
    last_word = before.rsplit(" ", 1)[-1].rstrip(".").lower()
    if last_word in _ABBREVIATIONS:
        return True
    # Ordinals such as "3. gün" or dates "14.10.2026"
    return last_word.isdigit() and before.endswith(".")


def _is_suspension(m: re.Match, paragraph: str) -> bool:
    # "Peki… neden?" — an ellipsis followed by a lowercase word continues the sentence.
    nxt = paragraph[m.end():m.end() + 1]
    return m[1].rstrip("\"'”’»)").endswith(("…", "...")) and nxt.islower()


def _paragraph_sentences(paragraph: str) -> list[str]:
    sentences: list[str] = []
    start = 0
    for m in _SENTENCE_END.finditer(paragraph):
        candidate = paragraph[start:m.end(1)]
        if _is_false_boundary(candidate) or _is_suspension(m, paragraph):
            continue
        sentences.append(candidate.strip())
        start = m.end()
    tail = paragraph[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def split_sentences(text: str) -> list[str]:
    return [s for p in _normalize(text).split("\n") for s in _paragraph_sentences(p)]


def _split_long(sentence: str, max_chars: int) -> list[str]:
    parts: list[str] = []
    current = ""
    for piece in _SOFT_BREAK.split(sentence):
        for word in piece.split(" ") if len(piece) > max_chars else [piece]:
            joined = f"{current} {word}".strip()
            if current and len(joined) > max_chars:
                parts.append(current)
                current = word
            else:
                current = joined
    if current:
        parts.append(current)
    return parts


@dataclass(frozen=True)
class Chunk:
    text: str
    pause_factor: float  # multiplier for the pause inserted after this chunk


def _ends_with_ellipsis(text: str) -> bool:
    return text.rstrip("\"'”’») ").endswith(("…", "..."))


def _pause_factor(text: str, paragraph_end: bool) -> float:
    if paragraph_end:
        return 2.0
    if _ends_with_ellipsis(text):
        return 1.6
    if text.rstrip("\"'”’») ").endswith(("?", "!")):
        return 1.25
    return 1.0


def _pack_paragraph(paragraph: str, target: int, max_chars: int, min_chars: int) -> list[str]:
    units = [u for s in _paragraph_sentences(paragraph) for u in (_split_long(s, max_chars) if len(s) > max_chars else [s])]
    packed: list[str] = []
    for unit in units:
        # Group sentences for natural prosody; always break after "…" to keep its dramatic pause.
        if packed and len(packed[-1]) + 1 + len(unit) <= target and not _ends_with_ellipsis(packed[-1]):
            packed[-1] = f"{packed[-1]} {unit}"
        else:
            packed.append(unit)
    # The model is unstable on very short inputs: merge them into a neighbour.
    merged: list[str] = []
    for chunk in packed:
        if merged and len(merged[-1]) < min_chars and len(merged[-1]) + 1 + len(chunk) <= max_chars:
            merged[-1] = f"{merged[-1]} {chunk}"
        else:
            merged.append(chunk)
    if len(merged) > 1 and len(merged[-1]) < min_chars and len(merged[-2]) + 1 + len(merged[-1]) <= max_chars:
        merged[-2:] = [f"{merged[-2]} {merged[-1]}"]
    return merged


def split_chunks(
    text: str,
    target_chars: int = config.TARGET_CHUNK_CHARS,
    max_chars: int = config.MAX_CHUNK_CHARS,
    min_chars: int = config.MIN_CHUNK_CHARS,
) -> list[Chunk]:
    """Split text into synthesis chunks of a few sentences each.

    Sentences are grouped up to ``target_chars`` so the model keeps prosody across them;
    chunks never cross paragraphs and sentences longer than ``max_chars`` are split at commas,
    then words. Each chunk carries a pause factor derived from its ending punctuation.
    """
    target_chars = min(target_chars, max_chars)
    paragraphs = _normalize(text).split("\n") if text.strip() else []
    chunks: list[Chunk] = []
    for p_index, paragraph in enumerate(paragraphs):
        packed = _pack_paragraph(paragraph, target_chars, max_chars, min_chars)
        for c_index, chunk in enumerate(packed):
            paragraph_end = c_index == len(packed) - 1 and p_index < len(paragraphs) - 1
            chunks.append(Chunk(chunk, _pause_factor(chunk, paragraph_end)))
    return chunks


def split_text(text: str, **kwargs) -> list[str]:
    return [c.text for c in split_chunks(text, **kwargs)]


def prepare_chunks(raw_text: str) -> list[Chunk]:
    """Full text pipeline used for synthesis: Turkish normalisation, then chunking."""
    return split_chunks(normalize_turkish(raw_text))
