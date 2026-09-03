# LinePatch 🩹

### Make copied PDF text readable before it enters your AI.

Copy once. See the patch. Paste clean text. **No cloud. No model. No silent rewrite.**

LinePatch is a tiny local CLI for the ugly text that appears after copying from a
PDF, browser reader, scan result, or two-column article. It repairs high-confidence
line-wraps, split words, and invisible copy artifacts while keeping lists, headings,
URLs, email addresses, and fenced code untouched.

## The 10-second demo

```text
# Research note
This paragraph was copied from a PDF and each
visual line became a new line. It also contains an inter-
national example and a nonbreaking space.
```

```console
$ linepatch examples/messy.txt --diff
--- examples/messy.txt
+++ linepatch (repaired)
@@
-This paragraph was copied from a PDF and each
-visual line became a new line. It also contains an inter-
-national example and a nonbreaking space.
+This paragraph was copied from a PDF and each visual line became a new line. It also contains an international example and a nonbreaking space.
```

```console
$ linepatch examples/messy.txt --output clean.txt
linepatch: wrote clean.txt (2 joined lines, 1 dehyphenated word, 1 normalized artifact)
```

Open `clean.txt`, review it, and paste it into your AI chat or notes app.

## Install

Requires Python 3.10 or newer.

```console
git clone https://github.com/juwonllee2024-dotcom/linepatch.git
cd linepatch
python -m pip install -e .
```

## Use it your way

Read a file and print repaired text:

```console
linepatch copied.txt
```

Use a pipe without contaminating stdout with status text:

```console
type copied.txt | linepatch - > clean.txt
```

Preview the exact change before accepting it:

```console
linepatch copied.txt --diff
```

Write only to an explicit destination. Existing files are protected unless you
say `--force`; the input file can never be the output file:

```console
linepatch copied.txt --output clean.txt
linepatch copied.txt --output clean.txt --force
```

For scripts, request a JSON report:

```console
linepatch copied.txt --json
```

Use `--check` in a workflow when any proposed repair should fail the check:

```console
linepatch copied.txt --check > clean.txt
```

LinePatch accepts UTF-8 input up to **10 MiB / 100,000 lines by default**. For
larger documents you can raise either limit up to the built-in safety caps of
64 MiB and 1,000,000 lines:

```console
linepatch copied.txt --max-input-bytes 33554432 --max-lines 250000 --diff
```

## What it changes

- Joins likely visual line wraps inside ordinary prose.
- Reconnects a word split at a line-ending hyphen when the next word starts in lowercase.
- Normalizes CRLF/CR, non-breaking spaces, soft hyphens, zero-width characters, and BOM artifacts.
- Preserves blank lines, Markdown headings and lists, blockquotes, tables, URLs, email addresses, horizontal rules, and fenced code blocks.
- Reports the repair counts so a human can decide whether to use the result.

LinePatch is deliberately conservative. It does **not** parse PDFs, reconstruct columns,
OCR images, access the clipboard, call a model, upload text, or edit a source file in
place. Paragraph recovery is a heuristic; `--diff` is the trust boundary. Terminal
control characters are escaped when repaired text is written to an interactive
terminal, and file writes use explicit destinations plus atomic replacement.

## Why local and open source?

Pasted research text can contain private notes, unpublished work, or credentials.
The core operation is deterministic and needs no server. Anyone can inspect the rules,
run them offline, and propose a fixture for a document shape LinePatch currently leaves
alone.

## Development

```console
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
mypy
python -m build
pip-audit --local
```

The full release checklist and one recorded real-input run are in
[`docs/verification.md`](docs/verification.md). See [`CONTRIBUTING.md`](CONTRIBUTING.md)
before opening a pull request.

## Roadmap

The next experiment is a tiny browser paste surface that reuses the same engine
through a local process. It will remain opt-in, show the diff, and never watch the
clipboard in the background. The current CLI is the complete v0.1.0 product.

## License

MIT — see [`LICENSE`](LICENSE).
