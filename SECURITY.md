# Security policy

## Scope

LinePatch is a local, deterministic text transformer. In v0.1.0 it does not
start a server, access the system clipboard, execute input as code, call a
network service, or upload document contents.

The CLI reads a UTF-8 file or stdin. It writes only when `--output` is supplied;
existing output files require `--force`, and the input path is always protected.
Input is read in chunks and bounded to 10 MiB / 100,000 lines by default, with
hard caps of 64 MiB / 1,000,000 lines. `--force` writes a same-directory
temporary file and atomically replaces a regular destination; symlink,
hard-link, and reparse-point destinations are rejected. Control characters are
escaped when output is sent to an interactive terminal.

## Reporting a vulnerability

Please report a security issue privately through
[GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/working-with-repository-security-advisories/about-repository-security-advisories).
Include the affected version, operating system, reproduction steps, and a
minimal non-sensitive sample. Do not attach secrets or private documents.

If private reporting is unavailable, open a public issue with only a safe,
sanitized description and ask for a private contact route. We will not ask you
to publish sensitive input.

## Security expectations for changes

- Keep input handling data-only; never add an implicit shell, browser, or
  clipboard action.
- Preserve explicit output paths and no-overwrite defaults.
- Add a regression test for any parser or boundary change.
- Do not commit sample credentials, personal documents, or telemetry.
