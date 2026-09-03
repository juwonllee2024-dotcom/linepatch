# LinePatch research note

Date: 2026-09-03
Decision: build a small, local, review-first MVP.

## The problem

People copy text from PDFs, scanned documents, browser readers, and two-column articles into an AI chat, notes app, or document. The copied text often contains hard line breaks at visual line wraps, split words, non-breaking spaces, and accidental blank lines. The user must repair it before the real task can start.

This is not a claim that every pasted line should be joined. PDF text extraction has no universal paragraph boundary, so a safe tool must make conservative guesses and show its changes. See [pypdf's extraction discussion](https://github.com/py-pdf/pypdf/blob/main/docs/user/extract-text.md) and the [Stack Overflow explanation of PDF line-wrap ambiguity](https://stackoverflow.com/questions/37535734/converting-pdf-to-text-without-the-wrapping-line-breaks).

## Four independent innovation questions

### 1. LinePatch — a reversible repair pass before paste

- **Fact:** Users repeatedly describe copied PDF text as broken by unwanted line breaks, and some currently paste through a URL bar or a small intermediary tool to remove them. Examples: [r/shortcuts](https://www.reddit.com/r/shortcuts/comments/1rpjubm/how_to_avoid_line_breaks_while_copy_pasting/), [r/MicrosoftWord](https://www.reddit.com/r/MicrosoftWord/comments/1nax4yt/tool_to_fix_messy_text_copied_from_pdf/), and [Stack Overflow](https://stackoverflow.com/questions/37535734/converting-pdf-to-text-without-the-wrapping-line-breaks).
- **Innovation hypothesis:** A local, deterministic “repair patch” that changes only high-confidence wraps—and exposes every change—can remove the annoying intermediary step without pretending to understand the whole document.
- **One difference:** It treats cleanup as a reviewable patch: preserve bullets, code, URLs, email addresses, headings, and intentional blank lines; report exactly what changed.
- **Smallest 7-day experiment:** Give five people a CLI/web build and ten messy samples. Measure whether they can accept the output without manual repair and whether the change preview earns trust.
- **First users:** Students, researchers, support writers, developers, and anyone who pastes PDFs into AI chats or notes.
- **Revenue hypothesis:** Keep the core MIT tool free; a future hosted/team policy pack or managed browser integration could be paid, but no revenue is assumed.

### 2. PortSonar — explain stale localhost processes

- **Fact:** Localhost process/port cleanup is a current developer pain, and [sonar](https://github.com/raskrebs/sonar) is a strong recent signal in that space.
- **Innovation hypothesis:** A process tree plus “why is this port alive?” explanation is safer than repeatedly killing a PID.
- **One difference:** Show parent/child lineage and a reversible stop plan before action.
- **Smallest 7-day experiment:** Ask developers to diagnose five stale ports; compare time-to-cause with `lsof`/Task Manager.
- **Decision:** **Reject today.** Strong pain, but the category is already legible and crowded; a new wrapper risks becoming a smaller [sonar](https://github.com/raskrebs/sonar).

### 3. MarkMerge — make browser bookmark export safe to merge

- **Fact:** Bookmark duplication and migration are recurring complaints; multiple open-source projects already sync, deduplicate, or convert bookmarks.
- **Innovation hypothesis:** A local “merge preview” with stable IDs and an undo file could make browser migration less destructive.
- **One difference:** Never overwrite the browser database; emit a reviewable merge plan and backup.
- **Smallest 7-day experiment:** Run it on three exported bookmark files and ask users to accept/reject every conflict.
- **Decision:** **Reject today.** There are many focused bookmark sync/merge tools, and this overlaps the existing browser-context portfolio.

### 4. DoneLedger — remember the last time a real-life task happened

- **Fact:** A highly upvoted self-hosting discussion asks for a simple “last time I did X” tracker: [r/selfhosted](https://www.reddit.com/r/selfhosted/comments/1tukylp/selfhosted_app_for_tracking_last_time_i_did_x/).
- **Innovation hypothesis:** A frictionless event log with plain-language prompts can beat heavyweight habit/task systems for irregular chores.
- **One difference:** Track elapsed time since an event, not streaks or scheduled tasks.
- **Smallest 7-day experiment:** Give ten users a local one-page app with three recurring chores and measure entries after one week.
- **Decision:** **Reject today.** The pain is real, but direct products such as [LastTime](https://apps.apple.com/us/app/lasttime/id6478228985) and [Streakless](https://play.google.com/store/apps/details?id=com.streakless) already own the obvious framing.

## Candidate score

Scores are 1–5, based on today’s evidence; they are prioritization estimates, not market forecasts.

| Candidate | Pain | Novelty | Build today | Shareability | Open-source fit | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LinePatch | 5 | 3 | 5 | 4 | 5 | **22/25** |
| PortSonar | 4 | 2 | 5 | 3 | 4 | 18/25 |
| DoneLedger | 4 | 2 | 4 | 4 | 3 | 17/25 |
| MarkMerge | 3 | 2 | 4 | 3 | 4 | 16/25 |

## Decision and boundary

Build **LinePatch** as a separate public repository. It will accept a text file or stdin, normalize only high-confidence artifacts, preserve code-like and list-like lines, and write output only when the user explicitly chooses a destination. The MVP will not read the system clipboard, upload content, call an AI model, or modify source files in place.

The product is intentionally narrower than a PDF parser. Existing extractors such as [pdftext](https://github.com/datalab-to/pdftext) and [pdfplumber](https://github.com/norpie/pdfplumber) solve extraction; LinePatch starts after extraction, when a human already has text and wants a safe, readable paste.

## Positioning test

One-line promise: **“Make copied PDF text readable before it enters your AI.”**

The first distribution test is a before/after GIF or terminal recording using real-looking but non-sensitive sample text, posted where researchers, students, and developers already discuss PDF copy/paste friction. The success signal is not stars; it is whether a stranger can install it, understand the diff, and use the cleaned result in under two minutes.
