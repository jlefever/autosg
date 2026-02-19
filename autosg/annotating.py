"""Encoding detection, annotation styles, and source annotation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .parsing import parse_identifiers

# ---------------------------------------------------------------------------
# Encoding detection
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FileEncoding:
    """Detected encoding of a source file."""

    encoding: str  # e.g. "utf-8", "utf-16-le", "utf-32-be"
    bom: bytes  # BOM bytes to preserve on write-back, or b"" for none


# Ordered so UTF-32 LE is checked before UTF-16 LE (shared \xff\xfe prefix).
_BOM_TABLE: list[tuple[bytes, str]] = [
    (b"\xff\xfe\x00\x00", "utf-32-le"),
    (b"\x00\x00\xfe\xff", "utf-32-be"),
    (b"\xff\xfe", "utf-16-le"),
    (b"\xfe\xff", "utf-16-be"),
    (b"\xef\xbb\xbf", "utf-8"),
]


def detect_encoding(raw: bytes) -> FileEncoding | None:
    """Detect file encoding via BOM, falling back to UTF-8.

    Returns *None* if the encoding is unsupported (not valid UTF-8 and
    no recognised BOM).
    """
    for bom, encoding in _BOM_TABLE:
        if raw.startswith(bom):
            return FileEncoding(encoding, bom)
    # No BOM — try UTF-8
    try:
        raw.decode("utf-8")
        return FileEncoding("utf-8", b"")
    except UnicodeDecodeError:
        return None


def read_source_utf8(source_path: Path) -> tuple[bytes, FileEncoding] | None:
    """Read a source file and return (utf8_bytes, encoding_info).

    The BOM is stripped from the returned bytes.  UTF-16/32 content is
    transcoded to UTF-8.  Returns *None* for unsupported encodings.
    """
    raw: bytes = source_path.read_bytes()
    enc: FileEncoding | None = detect_encoding(raw)
    if enc is None:
        return None
    payload: bytes = raw[len(enc.bom) :]
    if enc.encoding == "utf-8":
        return payload, enc
    text: str = payload.decode(enc.encoding)
    return text.encode("utf-8"), enc


def encode_output(utf8_bytes: bytes, enc: FileEncoding) -> bytes:
    """Encode UTF-8 bytes back to the original encoding, prepending the BOM."""
    if enc.encoding == "utf-8":
        return enc.bom + utf8_bytes
    return enc.bom + utf8_bytes.decode("utf-8").encode(enc.encoding)


# ---------------------------------------------------------------------------
# Annotation styles
# ---------------------------------------------------------------------------

_SUPERSCRIPT_DIGITS: str = "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079"


def _to_superscript(n: int) -> str:
    return "".join(_SUPERSCRIPT_DIGITS[int(d)] for d in str(n))


@dataclass(frozen=True)
class AnnotationStyle:
    """Defines how an identifier is annotated with its ID."""

    name: str
    open: str
    sep: str
    close: str
    superscript: bool = False

    def format(self, ident_id: int, text: str) -> str:
        if self.superscript:
            return text + _to_superscript(ident_id)
        return f"{self.open}{ident_id}{self.sep}{text}{self.close}"


ANNOTATION_STYLES: dict[str, AnnotationStyle] = {
    s.name: s
    for s in [
        AnnotationStyle("guillemet-pipe", "\u00ab", "|", "\u00bb"),
        AnnotationStyle("guillemet-colon", "\u00ab", ":", "\u00bb"),
        AnnotationStyle("angle-pipe", "\u27e8", "|", "\u27e9"),
        AnnotationStyle("angle-colon", "\u27e8", ":", "\u27e9"),
        AnnotationStyle("section-dot", "\u00a7", "\u00b7", "\u00a7"),
        AnnotationStyle("curly-ratio", "\u2983", "\u2236", "\u2984"),
        AnnotationStyle("superscript", "", "", "", superscript=True),
    ]
}

DEFAULT_STYLE: str = "guillemet-pipe"


# ---------------------------------------------------------------------------
# Annotate logic
# ---------------------------------------------------------------------------


def annotate_source(
    utf8_bytes: bytes,
    language: str,
    style: AnnotationStyle,
    start_id: int,
) -> tuple[bytes, int]:
    """Annotate identifiers in UTF-8 source bytes.

    Returns (annotated_utf8_bytes, next_available_id).
    All splicing is done on UTF-8 bytes so tree-sitter's byte offsets
    stay aligned.
    """
    identifiers: list[tuple[int, int, str]] = parse_identifiers(utf8_bytes, language)
    lines: list[bytes] = utf8_bytes.splitlines(keepends=True)

    # Build {0-indexed row: [(byte_col_0indexed, text, global_id), ...]}
    by_row: dict[int, list[tuple[int, str, int]]] = defaultdict(list)
    current_id: int = start_id
    for row_1, col_1, text in identifiers:
        by_row[row_1 - 1].append((col_1 - 1, text, current_id))
        current_id += 1

    # Process each row, replacing identifiers right-to-left in bytes
    for row_idx, entries in by_row.items():
        line: bytes = lines[row_idx]
        for byte_col, text, ident_id in sorted(entries, key=lambda e: e[0], reverse=True):
            text_bytes: bytes = text.encode("utf-8")
            replacement: bytes = style.format(ident_id, text).encode("utf-8")
            line = line[:byte_col] + replacement + line[byte_col + len(text_bytes) :]
        lines[row_idx] = line

    return b"".join(lines), current_id
