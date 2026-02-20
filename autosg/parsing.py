"""Language detection and tree-sitter parsing helpers."""

from __future__ import annotations

import warnings
from collections.abc import Iterator
from pathlib import Path
from typing import cast

from tree_sitter import Node, Parser, Tree

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    from tree_sitter_languages import get_parser # type: ignore

# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

FILENAME_TO_LANGUAGE: dict[str, str] = {
    "Dockerfile": "dockerfile",
    "GNUmakefile": "make",
    "Makefile": "make",
    "go.mod": "gomod",
    "makefile": "make",
}

EXTENSION_TO_LANGUAGE: dict[str, str] = {
    # bash
    ".bash": "bash",
    ".sh": "bash",
    ".zsh": "bash",
    # c
    ".c": "c",
    ".h": "c",
    # c_sharp
    ".cs": "c_sharp",
    # commonlisp
    ".cl": "commonlisp",
    ".lisp": "commonlisp",
    ".lsp": "commonlisp",
    # cpp
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hh": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    # css
    ".css": "css",
    # dot
    ".dot": "dot",
    ".gv": "dot",
    # elisp
    ".el": "elisp",
    # elixir
    ".ex": "elixir",
    ".exs": "elixir",
    # elm
    ".elm": "elm",
    # erlang
    ".erl": "erlang",
    ".hrl": "erlang",
    # fortran
    ".f": "fortran",
    ".f03": "fortran",
    ".f08": "fortran",
    ".f90": "fortran",
    ".f95": "fortran",
    ".for": "fortran",
    ".fpp": "fortran",
    # go
    ".go": "go",
    # hack
    ".hack": "hack",
    # haskell
    ".hs": "haskell",
    ".lhs": "haskell",
    # hcl
    ".hcl": "hcl",
    ".tf": "hcl",
    ".tfvars": "hcl",
    # html
    ".htm": "html",
    ".html": "html",
    # java
    ".java": "java",
    # javascript
    ".cjs": "javascript",
    ".js": "javascript",
    ".mjs": "javascript",
    # json
    ".json": "json",
    # julia
    ".jl": "julia",
    # kotlin
    ".kt": "kotlin",
    ".kts": "kotlin",
    # lua
    ".lua": "lua",
    # markdown
    ".markdown": "markdown",
    ".md": "markdown",
    # objc
    ".m": "objc",
    # ocaml
    ".ml": "ocaml",
    ".mli": "ocaml",
    # perl
    ".pl": "perl",
    ".pm": "perl",
    # php
    ".php": "php",
    # python
    ".py": "python",
    ".pyi": "python",
    # ql
    ".ql": "ql",
    ".qll": "ql",
    # r
    ".R": "r",
    ".r": "r",
    # rst
    ".rst": "rst",
    # ruby
    ".rb": "ruby",
    # rust
    ".rs": "rust",
    # scala
    ".sc": "scala",
    ".scala": "scala",
    # sql
    ".sql": "sql",
    # toml
    ".toml": "toml",
    # tsx
    ".tsx": "tsx",
    # typescript
    ".ts": "typescript",
    # yaml
    ".yaml": "yaml",
    ".yml": "yaml",
}


def detect_language(path: Path) -> str | None:
    """Detect tree-sitter language name from a file path."""
    return FILENAME_TO_LANGUAGE.get(path.name) or EXTENSION_TO_LANGUAGE.get(path.suffix)


# ---------------------------------------------------------------------------
# Per-language identifier node types
# ---------------------------------------------------------------------------

_DEFAULT_IDENT: frozenset[str] = frozenset({"identifier"})

LANGUAGE_IDENTIFIER_TYPES: dict[str, frozenset[str]] = {
    "bash": frozenset({"variable_name"}),
    "c": frozenset({"identifier", "field_identifier", "type_identifier"}),
    "c_sharp": _DEFAULT_IDENT,
    "commonlisp": frozenset({"sym_lit"}),
    "cpp": frozenset({"identifier", "field_identifier", "namespace_identifier", "type_identifier"}),
    "dot": _DEFAULT_IDENT,
    "elisp": frozenset({"symbol"}),
    "elixir": _DEFAULT_IDENT,
    "elm": frozenset({"lower_case_identifier", "upper_case_identifier"}),
    "erlang": frozenset({"atom", "var"}),
    "fortran": _DEFAULT_IDENT,
    "go": frozenset({"identifier", "field_identifier", "package_identifier", "type_identifier"}),
    "hack": _DEFAULT_IDENT,
    "haskell": frozenset({"variable", "type"}),
    "hcl": _DEFAULT_IDENT,
    "java": frozenset({"identifier", "type_identifier"}),
    "javascript": frozenset({"identifier", "property_identifier"}),
    "jsdoc": _DEFAULT_IDENT,
    "julia": _DEFAULT_IDENT,
    "kotlin": frozenset({"simple_identifier", "type_identifier"}),
    "lua": _DEFAULT_IDENT,
    "objc": _DEFAULT_IDENT,
    "ocaml": frozenset({"value_name", "value_pattern", "module_name", "type_constructor"}),
    "perl": _DEFAULT_IDENT,
    "php": frozenset({"name"}),
    "python": _DEFAULT_IDENT,
    "ql": frozenset({"simpleId", "predicateName", "className"}),
    "r": _DEFAULT_IDENT,
    "ruby": _DEFAULT_IDENT,
    "rust": frozenset({"identifier", "field_identifier", "type_identifier"}),
    "scala": frozenset({"identifier", "type_identifier", "operator_identifier"}),
    "sql": _DEFAULT_IDENT,
    "sqlite": _DEFAULT_IDENT,
    "tsx": frozenset({"identifier", "property_identifier", "type_identifier"}),
    "typescript": frozenset({"identifier", "property_identifier", "type_identifier"}),
}


# ---------------------------------------------------------------------------
# Tree-sitter parsing helpers
# ---------------------------------------------------------------------------


def collect_identifiers(node: Node, ident_types: frozenset[str]) -> Iterator[Node]:
    """Recursively collect all leaf identifier nodes from the syntax tree."""
    if node.child_count == 0 and node.type in ident_types:
        yield node
    for child in node.children:
        yield from collect_identifiers(child, ident_types)


def parse_identifiers(source_utf8: bytes, language: str) -> list[tuple[int, int, str]]:
    """Parse UTF-8 source bytes and return identifiers as (row, byte_col, text).

    Row is 1-indexed. byte_col is the 1-indexed byte offset within the line
    (relative to the BOM-stripped UTF-8 content). Use ``byte_col_to_char_col``
    to convert to a character column for display.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        parser: Parser = cast(Parser, get_parser(language))
    ident_types: frozenset[str] = LANGUAGE_IDENTIFIER_TYPES.get(language, _DEFAULT_IDENT)
    tree: Tree = parser.parse(source_utf8)
    identifiers: list[tuple[int, int, str]] = []
    for node in collect_identifiers(tree.root_node, ident_types):
        row: int = node.start_point[0] + 1  # 1-indexed
        byte_col: int = node.start_point[1] + 1  # 1-indexed byte offset
        text: str = node.text.decode()
        identifiers.append((row, byte_col, text))
    return identifiers


def byte_col_to_char_col(line_bytes: bytes, byte_col_1: int) -> int:
    """Convert a 1-indexed byte offset to a 1-indexed character column."""
    return len(line_bytes[: byte_col_1 - 1].decode("utf-8", errors="replace")) + 1
