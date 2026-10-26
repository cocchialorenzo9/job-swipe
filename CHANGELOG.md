# Changelog

## 0.3.0

Open source and safer to share.

- **License**: MIT. The interview adapts Matt Pocock's MIT-licensed `grilling` skill (see THIRD_PARTY_NOTICES.md).
- **Web pages are treated as untrusted.** The search and the CV task ignore instructions hidden in job pages, skip
  postings that try to make them act, and tell you in the notification ("Skipped 1 posting that looked
  suspicious…"). Your name, contact details and CV text never go into searches, links or forms, and the tasks make
  no other network requests from the command line.
- **CV builder**: headlines with `%` or `#` (for example "Growth PM | 100% remote") no longer break the build.
  Contact entries that aren't a clean email or web address are shown as plain text and listed in the build report.
  The builder's Python packages are pinned to known major versions.
- **Board CV viewer** (new boards only, see below): pdf.js 6.4.299 replaces 3.11.174 (CVE-2024-4367), and it is
  checked against pinned hashes before it runs. Clear messages while a CV opens, a simpler preview with "Open full
  PDF" on devices that can't run the full viewer (iOS before 17.4), a plain explanation when a CV has expired,
  keyboard focus that stays in the viewer, bigger tap targets, and the board version under ⚙.
- **Existing boards keep their old page.** The board page is copied when a board is made, so boards created before
  0.3.0 keep the old CV viewer (no "Board version" row under ⚙). Everything else in this release reaches them. The
  old viewer's pdf.js issue needs a malicious PDF, and the CVs on a board are built by your own CV task, so the risk
  is low; you don't need to do anything. Updating existing boards in place, without losing their jobs, is on the
  roadmap.
- Repo: CI, browser tests for the CV viewer, contributing guide, security policy, issue and pull request templates.

## 0.2.x

Marketplace manifest, CV expiry that never deletes the board, write-conflict handling, a sturdier CV builder setup,
and the configure skill renamed to `job-swipe-configure`.
