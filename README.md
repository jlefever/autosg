# autosg

A tool that uses [tree-sitter](https://tree-sitter.github.io/) to parse source files, extract identifiers, and produce annotated copies where each identifier is tagged with a unique numeric ID.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```
python -m autosg <command> [options] PATHS...
```

### `dump-identifiers`

Extract all identifiers to CSV.

```bash
# Dump to stdout
python -m autosg dump-identifiers examples/java/Example.java

# Dump recursively to a file
python -m autosg dump-identifiers -r examples/ -o output.csv
```

Output columns: `id`, `path`, `row`, `col`, `text`. Row and col are 1-indexed. Col reports character position (Unicode code points), matching VS Code's status bar.

```
id,path,row,col,text
0,examples/java/Example.java,1,9,com
1,examples/java/Example.java,1,13,example
2,examples/java/Example.java,3,8,java
3,examples/java/Example.java,3,13,util
4,examples/java/Example.java,3,18,List
...
```

### `annotate-files`

Produce `.annotated` copies of source files with each identifier wrapped in a style marker and its ID.

```bash
# Annotate a single file (default guillemet-pipe style)
python -m autosg annotate-files examples/java/Example.java

# Annotate recursively with a specific style
python -m autosg annotate-files -r examples/ --style superscript

# Remove all .annotated files
python -m autosg annotate-files --clean -r examples/
```

#### Example: `guillemet-pipe` (default)

```java
package «0|com».«1|example»;

import «2|java».«3|util».«4|List»;

public class «8|Example» {
    private int «9|count»;

    public «12|Example»(«13|String» «14|name») {
        this.«15|count» = 0;
    }
}
```

#### Example: `superscript`

```java
package com⁰.example¹;

import java².util³.List⁴;

public class Example⁸ {
    private int count⁹;

    public Example¹²(String¹³ name¹⁴) {
        this.count¹⁵ = 0;
    }
}
```

#### All annotation styles

| Name | Format | Example |
|---|---|---|
| `guillemet-pipe` | `«id\|text»` | `«3|count»` |
| `guillemet-colon` | `«id:text»` | `«3:count»` |
| `angle-pipe` | `⟨id\|text⟩` | `⟨3\|count⟩` |
| `angle-colon` | `⟨id:text⟩` | `⟨3:count⟩` |
| `section-dot` | `§id·text§` | `§3·count§` |
| `curly-ratio` | `⦃id∶text⦄` | `⦃3∶count⦄` |
| `superscript` | `textⁱᵈ` | `count³` |

## Supported languages

autosg supports 46 languages via tree-sitter-languages, with per-language identifier node types for accurate extraction:

Bash, C, C#, C++, Common Lisp, CSS, DOT, Elisp, Elixir, Elm, Erlang, Fortran, Go, Hack, Haskell, HCL/Terraform, HTML, Java, JavaScript, JSON, Julia, Kotlin, Lua, Markdown, Objective-C, OCaml, Perl, PHP, Python, QL, R, reStructuredText, Ruby, Rust, Scala, SQL, TOML, TSX, TypeScript, YAML.

Language is auto-detected from the file extension or filename.

## Encoding support

Files are auto-detected and transcoded for parsing:

- **UTF-8** (with or without BOM)
- **UTF-16** LE/BE (BOM required)
- **UTF-32** LE/BE (BOM required)

Annotated output preserves the original encoding and BOM. Files with unsupported encodings (e.g. legacy Japanese) are warned and skipped.

## Project structure

```
autosg/
├── __init__.py       # package marker
├── __main__.py       # CLI entry point (click)
├── annotating.py     # encoding detection, annotation styles, annotate logic
└── parsing.py        # language detection, identifier types, tree-sitter parsing
```
