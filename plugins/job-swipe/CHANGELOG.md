# Changelog

## 0.4.0

The plugin now ships only instructions and pictures, no code, so it can be listed in the Claude plugin directory.

- **Your board** is now built by Claude from a written design (`references/board-spec.md`), with screenshots to
  match. It looks and works like before. Boards made with an earlier version keep working: the next time you run
  `/job-swipe-configure`, Claude offers to rebuild yours, says what's new and what could go wrong, and keeps your
  jobs, swipes, notes, CVs and link.
- **Tailored CVs** are now written by Claude directly from your CV details (`skills/tailor-cvs/references/cv-build.md`),
  with the same look, page fitting and text check as before. Nothing is installed from PyPI any more; LaTeX and
  poppler are still installed with `apt` where they're missing.
- **Safer CV builds**: every piece of text is escaped, only a short list of LaTeX commands is allowed in the CV, and
  LaTeX runs with shell commands off and file access limited to the build folder.
- **Scheduled tasks only use the installed plugin.** They no longer download Job Swipe from GitHub when the
  plugin is missing; they send a notification saying so instead. `/job-swipe-configure` updates older tasks for
  you. The README's "Can't add plugins?" route is gone for the same reason.
- The changelog now lives in the plugin folder, so Claude can read it when it offers a board rebuild.

## 0.3.3

- **Privacy section**: the README now says that Job Swipe has no server and reads no API keys, tokens, passwords or cookies. It also lists what the CV builder may install (`jinja2` and `pyyaml` from PyPI, and LaTeX and poppler with `apt`), where the fallback venv lives, and that those services see only package names.

## 0.3.2

- **Privacy link**: `plugin.json` now has a `privacyPolicyUrl` pointing to the README's "Your data and privacy" section, so the plugin directory can link to it.

## 0.3.1

- **Icon**: the plugin now ships a listing icon (`.claude-plugin/icon.png`, 1024 × 1024 PNG): a job card mid-swipe with a red heart badge.

## 0.3.0

Open source and safer to share.

- **License**: MIT. The interview adapts Matt Pocock's MIT-licensed `grilling` skill (see THIRD_PARTY_NOTICES.md).
- **Web pages are treated as untrusted.** The search and the CV task ignore instructions hidden in job pages, skip
  postings that try to make them act, and tell you in the notification ("Skipped 1 posting that looked
  suspicious…"). Claude is told never to put your name, contact details or CV text into searches, links or forms,
  and not to make network requests from the command line apart from the CV builder's installs. These are
  instructions, not a sandbox: they lower the risk, they can't rule it out.
- **Your data**: the README explains what Job Swipe keeps, who sees it, for how long, and how to remove it. Turning
  CVs off or pausing now deletes the CVs still on your board (before, they stayed on the board indefinitely).
- **CV builder**: headlines with `%` or `#` (for example "Growth PM | 100% remote") no longer break the build.
  Contact entries that aren't a clean email or web address are shown as plain text and listed in the build report.
  The builder's Python packages are pinned to known major versions.
- **Board CV viewer** (new boards only, see below): pdf.js 6.4.299 replaces 3.11.174 (CVE-2024-4367), and it is
  checked against pinned hashes before it runs. Clear messages while a CV opens, a simpler preview with "Open full
  PDF" on devices that can't run the full viewer (iOS before 17.4), a plain explanation when a CV has expired,
  keyboard focus that stays in the viewer, bigger tap targets, and the board version under ⚙.
- **Swipe notes** (new boards only): after each swipe the board asks "why?" about the job you just judged, and Enter
  saves it. You can still type a note before swiping. "Don't ask again" turns the question off, and ⚙ → Swipe notes
  turns it back on. Liked and passed jobs show your note and let you edit it.
- **"Already applied"** is now a labelled button on the card (bottom left), next to "View full posting" (bottom right),
  instead of the ✓ between the swipe buttons, which read as "yes". Applied jobs get their own **Applied** tab under ♥,
  with their CV and note, and "Move to interested" if you tapped it by mistake.
- **Existing boards keep their old page.** The board page is copied when a board is made, so boards created before
  0.3.0 keep the old CV viewer (no "Board version" row under ⚙). Everything else in this release reaches them. The
  old viewer's pdf.js issue needs a malicious PDF, and the CVs on a board are built by your own CV task, so the risk
  is low; you don't need to do anything. Updating existing boards in place, without losing their jobs, is on the
  roadmap.
- Repo: CI, browser tests for the CV viewer, contributing guide, security policy, issue and pull request templates.

## 0.2.x

Marketplace manifest, CV expiry that never deletes the board, write-conflict handling, a sturdier CV builder setup,
and the configure skill renamed to `job-swipe-configure`.
