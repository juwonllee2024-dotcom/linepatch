# Verification record

Status: release candidate; local and security evidence are complete before
publishing `v0.1.0`.

## Scope

The recorded scenario uses the synthetic fixture in `examples/messy.txt` and
contains no private text. The input includes a wrapped paragraph, a split word,
a non-breaking space, list items, and a URL.

## TDD evidence

- RED: the initial test run failed because `linepatch` had no implementation.
- GREEN: the minimal engine and CLI were added, then the same suite passed.
- Regression: tests cover explicit output, no-overwrite defaults, same-file and
  link protection, terminal-control escaping, input limits, and `--force`'s
  atomic replacement path.

## Fresh command evidence

Run these commands from the repository root after a clean checkout:

```text
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
mypy
python -m compileall -q src tests
python -m build
pip-audit --local
git diff --check
```

Expected release-candidate result on Windows with Python 3.11:

- `python -m unittest discover -s tests -v`: **15 tests run; 14 passed and 1
  symlink test skipped** when Windows symlink privilege is unavailable.
- `ruff check .`: exit 0, no findings.
- `ruff format --check .`: every tracked Python file already formatted.
- `mypy`: no issues found.
- `python -m compileall -q src tests`: exit 0.
- `python -m build`: sdist and wheel built successfully.
- `pip-audit --local`: no known vulnerabilities in installed dependencies;
  local unpublished packages may be reported as skipped.
- `git diff --check`: exit 0.

The repository also runs the same checks on Python 3.10, 3.11, 3.12, and 3.13
through [the pinned GitHub Actions workflow](../.github/workflows/ci.yml).

## Security evidence

The post-hardening Codex Security standard scan completed against the complete
repository snapshot and explicitly checked:

- same-file, hard-link, symlink, reparse-point, and output-write race behavior;
- terminal control-character handling;
- bounded, chunked input and parser behavior on long lines;
- immutable action references and exact development dependency pins.

Scan ID: `81798a3c-279a-4336-95b5-b54fd9432e66`.

Snapshot digest:
`codex-security-snapshot/v1:sha256:97b3ddf06920939af88f34d4ff0f1ac838d531fc2e7b35d0bdc9afc811e20f3b`.

Result: **complete coverage of 19 files; 0 reportable findings**. The
canonical report was generated from the scan workbench. TAC access was
**unavailable** because `connector_openai_codex_security_access` was not
connected; no protected result was inferred from that absence.

## End-to-end record

Command:

```text
linepatch examples/messy.txt --output .verification-clean.txt
```

Observed result: `linepatch: wrote .verification-clean.txt (2 joined lines, 1
dehyphenated word, 1 normalized artifact)`. The output must match
`examples/clean.txt` byte-for-byte. The temporary output is deleted after the
hash is recorded; it is never the source fixture.

SHA-256 of the recorded run output:

```text
71702da4d7c8a66ff047f44194350f4820509c85433f4158efa2e412e662a1c7  .verification-clean.txt
```

The temporary file was removed after the comparison. The exact package hashes
below were also verified against the digests returned by GitHub for the
published release assets.

## Release identity

- Release commit: `2407e279530a57db3444abd3a78ac5cd93d2b255`.
- CI run: [33790287378](https://github.com/juwonllee2024-dotcom/linepatch/actions/runs/33790287378)
  — Python 3.10, 3.11, 3.12, and 3.13 all passed.
- Release: [v0.1.0](https://github.com/juwonllee2024-dotcom/linepatch/releases/tag/v0.1.0).
- Package SHA-256:
  - `linepatch-0.1.0-py3-none-any.whl`:
    `319039a3157206de308f0cbc121871866f32e7d899e9a7fd4f5ec2807b9b89a1`
  - `linepatch-0.1.0.tar.gz`:
    `ef01934880e0d57e86138d6b0ab4b1532c582a9e22a859829de826253de73e88`
