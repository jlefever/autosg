"""CLI entry point for autosg (python -m autosg)."""

from __future__ import annotations

import csv
import json
import os
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, TextIO

import click

from .annotating import (
    FileEncoding,
    annotate_source,
    encode_output,
    read_source_utf8,
)
from .parsing import byte_col_to_char_col, detect_language, parse_identifiers

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

ANNOTATED_SUFFIX: str = ".annotated"


def resolve_paths(paths: tuple[Path, ...], recursive: bool) -> Iterator[Path]:
    """Expand directories into individual file paths."""
    for path in paths:
        if path.is_file():
            yield path
        elif path.is_dir():
            if recursive:
                yield from sorted(p for p in path.rglob("*") if p.is_file())
            else:
                yield from sorted(p for p in path.iterdir() if p.is_file())
        else:
            click.echo(f"Warning: {path} is not a file or directory, skipping.", err=True)


def resolve_source_paths(paths: tuple[Path, ...], recursive: bool) -> Iterator[Path]:
    """Like resolve_paths but skips .annotated files."""
    for path in resolve_paths(paths, recursive):
        if not path.name.endswith(ANNOTATED_SUFFIX):
            yield path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def common_options(f: Callable[..., object]) -> Callable[..., object]:
    """Shared PATHS argument and -r/--recursive option for all subcommands."""
    f = click.argument(
        "paths",
        nargs=-1,
        required=True,
        type=click.Path(exists=True, path_type=Path),
    )(f)
    f = click.option(
        "-r", "--recursive",
        is_flag=True,
        default=False,
        help="Recurse into directories.",
    )(f)
    return f


@click.group()
def cli() -> None:
    """Parse source files and annotate identifiers."""


@cli.command("dump-identifiers")
@common_options
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output CSV path (default: stdout).",
)
def dump_identifiers(paths: tuple[Path, ...], recursive: bool, output: Path | None) -> None:
    """Dump all identifiers to CSV."""
    out: TextIO
    if output is not None:
        out = open(output, "w", newline="")
    else:
        out = sys.stdout
    try:
        writer = csv.writer(out)
        writer.writerow(["id", "path", "row", "col", "text"])
        global_id: int = 0
        for file_path in resolve_source_paths(paths, recursive):
            language: str | None = detect_language(file_path)
            if language is None:
                click.echo(
                    f"Warning: unsupported file extension {file_path.suffix!r} "
                    f"for {file_path}, skipping.",
                    err=True,
                )
                continue
            result: tuple[bytes, FileEncoding] | None = read_source_utf8(file_path)
            if result is None:
                click.echo(
                    f"Warning: unsupported encoding for {file_path}, skipping.",
                    err=True,
                )
                continue
            utf8_bytes, _enc = result
            rel_path: str = os.path.relpath(file_path)
            source_lines: list[bytes] = utf8_bytes.splitlines()
            for row, byte_col, text in parse_identifiers(utf8_bytes, language):
                char_col: int = byte_col_to_char_col(source_lines[row - 1], byte_col)
                writer.writerow([global_id, rel_path, row, char_col, text])
                global_id += 1
    finally:
        if out is not sys.stdout:
            out.close()


@cli.command("annotate-files")
@common_options
@click.option(
    "--clean",
    is_flag=True,
    default=False,
    help="Remove .annotated files instead of creating them.",
)
def annotate_files(
    paths: tuple[Path, ...], recursive: bool, clean: bool,
) -> None:
    """Annotate identifiers in source files, producing .annotated copies."""
    if clean:
        removed: int = 0
        for path in paths:
            if path.is_file():
                annotated: Path = path.parent / (path.name + ANNOTATED_SUFFIX)
                if annotated.exists():
                    annotated.unlink()
                    removed += 1
            elif path.is_dir():
                pattern: str = "**/*" + ANNOTATED_SUFFIX if recursive else "*" + ANNOTATED_SUFFIX
                for annotated_file in sorted(path.glob(pattern)):
                    annotated_file.unlink()
                    removed += 1
        click.echo(f"Removed {removed} .annotated file(s).")
        return

    file_count: int = 0
    total_ids: int = 0
    for file_path in resolve_source_paths(paths, recursive):
        language: str | None = detect_language(file_path)
        if language is None:
            click.echo(
                f"Warning: unsupported file extension {file_path.suffix!r} "
                f"for {file_path}, skipping.",
                err=True,
            )
            continue
        result: tuple[bytes, FileEncoding] | None = read_source_utf8(file_path)
        if result is None:
            click.echo(
                f"Warning: unsupported encoding for {file_path}, skipping.",
                err=True,
            )
            continue
        utf8_bytes, enc = result
        annotated_utf8, next_id = annotate_source(utf8_bytes, language, 0)
        out_path: Path = file_path.parent / (file_path.name + ANNOTATED_SUFFIX)
        out_path.write_bytes(encode_output(annotated_utf8, enc))
        file_count += 1
        total_ids += next_id
    click.echo(f"Annotated {file_count} file(s), {total_ids} identifier(s).")


@cli.command("llm-resolve")
@click.argument(
    "path",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--model",
    default=None,
    help="LiteLLM model identifier (default: anthropic/claude-sonnet-4-20250514).",
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Skip the disk cache and always call the LLM.",
)
def llm_resolve(path: Path, model: str | None, no_cache: bool) -> None:
    """Resolve identifier references using an LLM.

    Accepts a source file (annotated in memory) or an .annotated file.
    Prints the resolution JSON to stdout.
    """
    # Import lazily so litellm is not required for other subcommands.
    from . import llmresolver

    effective_model: str = model or llmresolver.DEFAULT_MODEL

    if path.name.endswith(ANNOTATED_SUFFIX):
        # Already annotated — read directly and infer language from base name.
        ann_result: tuple[bytes, FileEncoding] | None = read_source_utf8(path)
        if ann_result is None:
            click.echo(f"Error: unsupported encoding for {path}.", err=True)
            sys.exit(1)
        annotated_text: str = ann_result[0].decode("utf-8")
        base_name: str = path.name[: -len(ANNOTATED_SUFFIX)]
        language: str | None = detect_language(path.parent / base_name)
    else:
        # Source file — annotate in memory.
        language = detect_language(path)
        if language is None:
            click.echo(
                f"Error: unsupported file extension {path.suffix!r} for {path}.",
                err=True,
            )
            sys.exit(1)
        src_result: tuple[bytes, FileEncoding] | None = read_source_utf8(path)
        if src_result is None:
            click.echo(f"Error: unsupported encoding for {path}.", err=True)
            sys.exit(1)
        utf8_bytes, _enc = src_result
        annotated_utf8, _next_id = annotate_source(
            utf8_bytes, language, 0,
        )
        annotated_text = annotated_utf8.decode("utf-8")

    if language is None:
        click.echo(f"Error: cannot detect language for {path}.", err=True)
        sys.exit(1)

    try:
        result: dict[str, Any] = llmresolver.resolve(
            annotated_text, language, model=effective_model,
            use_cache=not no_cache,
        )
    except (RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc))
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    cli()
