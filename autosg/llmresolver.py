"""Resolve identifier references by sending annotated source to an LLM.

All LiteLLM usage is contained within this module.

Cache is stored in ``~/.cache/autosg/cache.db`` (SQLite).  The cache key
is (source_hash, model, prompt_version) so a new LLM call is made whenever
the annotated content, model, or prompt changes.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from litellm import completion # type: ignore
from litellm.exceptions import AuthenticationError as _AuthenticationError

load_dotenv()

DEFAULT_MODEL: str = "anthropic/claude-sonnet-4-20250514"

# Bump this when the prompt changes materially so cached results from an
# older prompt version are not reused.
PROMPT_VERSION: int = 2

CACHE_DIR: Path = Path.home() / ".cache" / "autosg"
CACHE_DB: Path = CACHE_DIR / "cache.db"

PROMPT_TEMPLATE: str = """\
Below is {lang} source code. Each identifier has been replaced with an \
annotated marker in the format `«id|name»`, where `id` is a unique integer \
and `name` is the original identifier text.

For each identifier, determine which other identifier(s) represent its \
definition or declaration — the target(s) an IDE's "Jump to Definition" \
would navigate to.

A reference may resolve to more than one target. For example, in C a \
function may have both a forward declaration and a later definition in the \
same file; both should be included. However, only return the direct \
declaration/definition sites — not other references to the same name.

Respond with **only** JSON in this exact structure (no commentary):

```json
{{
  "definitions": [
    [<reference_id>, <definition_id>],
    [<reference_id>, <definition_id>]
  ],
  "external": [<id>, <id>],
  "errors": [
    {{"id": <id>, "reason": "..."}}
  ]
}}
```

Field descriptions:
- `definitions` — pairs of [reference_id, definition_id] where both \
identifiers appear in this file. A reference_id may appear in multiple \
pairs if it resolves to more than one declaration/definition site. If an \
identifier *is* a definition (not a reference to one), omit it.
- `external` — identifiers whose definitions are outside this file (e.g. \
standard library, imports, other modules).
- `errors` — identifiers that cannot be resolved for any other reason, with \
a brief explanation.

```{lang}
{source}
```"""


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


def _open_cache_db() -> sqlite3.Connection:
    """Open (or create) the cache database and return a connection."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn: sqlite3.Connection = sqlite3.connect(CACHE_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cache ("
        "  source_hash     TEXT    NOT NULL,"
        "  model           TEXT    NOT NULL,"
        "  prompt_version  INTEGER NOT NULL,"
        "  response        TEXT    NOT NULL,"
        "  PRIMARY KEY (source_hash, model, prompt_version)"
        ")"
    )
    return conn


def _source_hash(annotated_source: str) -> str:
    """SHA-256 hex digest of the annotated source text."""
    return hashlib.sha256(annotated_source.encode("utf-8")).hexdigest()


def _cache_get(
    conn: sqlite3.Connection, source_hash: str, model: str,
) -> dict[str, Any] | None:
    """Return a cached response, or *None* on cache miss."""
    row = conn.execute(
        "SELECT response FROM cache"
        " WHERE source_hash = ? AND model = ? AND prompt_version = ?",
        (source_hash, model, PROMPT_VERSION),
    ).fetchone()
    if row is not None:
        return json.loads(row[0])  # type: ignore[no-any-return]
    return None


def _cache_put(
    conn: sqlite3.Connection,
    source_hash: str,
    model: str,
    response: dict[str, Any],
) -> None:
    """Store a response in the cache."""
    conn.execute(
        "INSERT OR REPLACE INTO cache"
        " (source_hash, model, prompt_version, response)"
        " VALUES (?, ?, ?, ?)",
        (source_hash, model, PROMPT_VERSION, json.dumps(response)),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Prompt / response helpers
# ---------------------------------------------------------------------------


def build_prompt(annotated_source: str, language: str) -> str:
    """Build the full prompt for the LLM."""
    return PROMPT_TEMPLATE.format(lang=language, source=annotated_source)


def _extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from LLM response text.

    Handles responses wrapped in markdown code fences as well as bare JSON.
    """
    # Try a ```json ... ``` code block first.
    match: re.Match[str] | None = re.search(
        r"```(?:json)?\s*\n(.*?)\n\s*```", text, re.DOTALL,
    )
    if match:
        return json.loads(match.group(1))  # type: ignore[no-any-return]
    # Fall back to the first top-level { ... } block.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))  # type: ignore[no-any-return]
    raise ValueError("No JSON object found in LLM response")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve(
    annotated_source: str,
    language: str,
    *,
    model: str = DEFAULT_MODEL,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Send annotated source to an LLM and return parsed resolution JSON.

    Returns a dict with keys ``definitions``, ``external``, ``errors``.
    Raises ``ValueError`` if the response cannot be parsed as JSON.
    """
    source_hash: str = _source_hash(annotated_source)

    conn: sqlite3.Connection | None = None
    if use_cache:
        conn = _open_cache_db()
        cached: dict[str, Any] | None = _cache_get(conn, source_hash, model)
        if cached is not None:
            conn.close()
            return cached

    prompt: str = build_prompt(annotated_source, language)
    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
    except _AuthenticationError as exc:
        raise RuntimeError(
            "Missing API key. Set ANTHROPIC_API_KEY in your environment "
            "(or the appropriate key for your chosen --model)."
        ) from exc
    content: str | None = response.choices[0].message.content # type: ignore
    if content is None:
        raise ValueError("LLM returned an empty response")
    result: dict[str, Any] = _extract_json(content) # type: ignore

    if use_cache:
        assert conn is not None
        _cache_put(conn, source_hash, model, result)
        conn.close()

    return result
