# Changelog

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
