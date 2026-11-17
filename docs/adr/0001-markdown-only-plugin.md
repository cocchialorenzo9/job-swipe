# The plugin ships no code: Claude builds the board and the CVs from written specs

The Claude plugin directory only accepts Markdown, text, JSON, YAML and images from publishers that aren't Verified organizations. We want Job Swipe listed, so the plugin no longer ships `board/job-swipe.html`, `build.py` or the LaTeX template. Instead:

- A **board spec** describes each person's board, and Claude builds the board from it at set-up time. The spec gives exact values in tables, behaviour as numbered steps, and screenshots as the visual reference. It contains no HTML, CSS or JS.
- The CV skill tells Claude how to write and check the LaTeX itself.

## Considered options

- **Download the code at run time** (from GitHub, or hidden in an image or a code block). Rejected: it goes around the directory's rule rather than meeting it, the code could change after review, and the directory already screens for it.
- **Swap the board for a built-in spreadsheet-style Artifact type.** Rejected: it's reliable, but it loses swiping, which is the product.
- **Keep the code and install only from our own marketplace.** Rejected because we want to be listed. It's still the fallback if we can't get listed.

## Consequences

- Two people's boards follow the same spec but are not the same file. A fix reaches existing boards only when they're rebuilt.
- The spec has to be precise enough that a build can be checked against it: an acceptance checklist plus the screenshots.
- Claude now writes each CV's LaTeX itself. The CV skill makes that safe with an escape table, an allowed list of commands for the document body, and a compile with shell escape off and file access restricted.
- Building a board, and every scheduled CV run, uses more of Claude's work than running a shipped file did.
- A CI check fails if the plugin folder holds any file type the directory refuses. Before each release, a board is built from the spec by hand and its screenshots are compared with the reference board's.
- If Job Swipe's publisher becomes a Verified organization, this decision can be reversed.
