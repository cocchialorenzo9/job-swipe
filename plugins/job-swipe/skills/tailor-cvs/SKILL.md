---
name: tailor-cvs
description: Builds a tailored, one-page, ATS-readable CV for each job a person liked on their Job Swipe board, using only the facts in their saved CV details, and attaches the PDFs to the board. Use when a scheduled task says "Job Swipe: make tailored CVs", or someone asks to "make my CVs now", "tailor my CV for the jobs I liked", or "make a CV for <company> from my board".
---

# Job Swipe — tailored CVs

Input: the board URL (from the arguments or the prompt; otherwise find the "Job Swipe" artifact with Artifact
`list`). On a schedule: never ask questions; make reasonable calls and finish.

Read `../../references/board-data.md` first: which tools touch the board, and how to handle a refused write.

This skill also needs the Artifact tool's `upload_asset` and `delete_asset` actions. If your Artifact tool lacks
either one (an older Claude app), change nothing on the board: send one notification "Your Claude app is too old to
attach CVs to your Job Swipe board: update the Claude app" and stop.

The builder lives next to this file in `cv/`: `build.py` (renders in the person's chosen style, enforces the page limit, checks the text like an application system),
`template.tex.j2` (the look), `examples/` (a sample master CV with the rules, and a sample job spec).

## 0. Quick exit (do this first, it keeps empty days cheap)

1. `read_db` `query` collection `jobs` where `status == "liked"`.
2. **To build**: liked docs with no `cvAssetId` and no `cvStatus`, and `swipedAt` within the last 14 days.
3. **To expire**: `read_db` `query` collection `jobs` where `cvAssetId != ""` — not filtered by status, since a
   liked job can later be passed or marked applied and its CV must still go. Keep those with `cvCreatedAt` older
   than 7 days.
4. **To clean up**: `read_db` `query` collection `jobs` where `cvDeleteAssetId != ""` (deletes that failed on an
   earlier run).
5. If all three lists are empty: stop now. No notification.

## 1. Expire week-old CVs

First unlink, then delete, so the board never points at a missing file and no file is ever forgotten:

1. For each doc to expire: `update` it (with `if_version`): `cvStatus: "expired"`, `cvExpiredAt` (ISO now),
   `cvUrl: ""`, `cvAssetId: ""`, `cvDeleteAssetId: <the old cvAssetId>`. Keep the rest. The doc now goes on the
   clean-up list.
2. For each doc on the clean-up list (including the ones just unlinked): Artifact `delete_asset` with `url` = board
   URL and `asset_id` = its `cvDeleteAssetId`. **Never use Artifact `delete` here: it deletes the whole board.**
   - Deleted, or the result says the asset does not exist → `update` the doc: `cvDeleteAssetId: {"__delete__": true}`.
   - Any other failure (permission, network, a board without stored files) → leave `cvDeleteAssetId` as it is so
     the next run tries again, and carry on.

## 2. Load the person's CV details

`read_db` `get` profile/me — if `cvEnabled` is false, stop after step 1. Then `get` profile/cv and write its
`masterYaml` to `master_cv.yaml` in your working directory. Missing → send one notification "Your Job Swipe CV
details are missing: ask Claude to 'configure Job Swipe'" and stop.

Rules that always hold (read the header of `cv/examples/master_cv.example.yaml` once):
- **Truth only.** Tailoring = choosing, ordering and re-wording facts that are in the master. Never invent skills,
  tools, numbers, titles, dates or languages. Never list anything in `never_list`.
- **Page limit and look come from `style`** in the master (agreed with the person). Never change the style per job. If it can't fit, list fewer bullets.
- **XYZ bullets** where the facts allow ("Accomplished X as measured by Y, by doing Z").

## 3. For each job (newest `swipedAt` first, at most 8 per run; the rest wait for the next run)

a. Read the posting at the doc's `url` (WebFetch). If it's clearly closed or gone, try the company careers page once;
   still gone → `update` the doc: `cvStatus: "skipped"`, `cvNote: "Posting no longer online (checked <date>)"`.
b. Pull 10–20 screening keywords (skills, tools, domain, methods), the seniority ask and the language ask.
c. Pick the master's `track` that fits best (or none). Write `jobs/<company>_<role>.yaml` following
   `cv/examples/job_spec.example.yaml`: headline and 2–3 line summary that mirror the posting's words truthfully;
   `roles` with the most relevant bullets first; `overrides` only to re-word the same facts toward the posting;
   `skills_front` to move matching skills forward; `keywords`. Plain text, no LaTeX.
d. Build: `python3 <this folder>/cv/build.py master_cv.yaml jobs/<spec>.yaml cv_out`, as a Bash call with
   `timeout` 600000: on a fresh machine the first build installs LaTeX, which takes a few minutes. If it says
   LaTeX is still installing, run the same command once more after 5 minutes; still failing → count it as a
   failed build.
   It must report `ATS text check: OK` and a page count within the limit (`style.max_pages`, default 1). Render once (`pdftoppm -r 70 -png <pdf> prev`) and look:
   no orphan one-word lines, nothing important dropped. Fix the spec, not the facts, and rebuild if needed.
e. Upload the PDF to the board: Artifact `upload_asset` with `url` = board URL and `file_path` = the PDF.
   Store the returned asset id as `cvAssetId` and its url as `cvUrl`, exactly as given.
f. `get` the doc again and `update` it (with `if_version`, retrying as in `../../references/board-data.md`): `cvStatus: "created"`,
   `cvAssetId`, `cvUrl`, `cvFileName` (the PDF's name), `cvCreatedAt` (ISO now), `cvNote` (≤ 200 characters, in
   the profile's `language`: the angle chosen + fit risks, e.g. posting keywords the CV could not truthfully
   cover, a language requirement, a big seniority gap).
g. If the doc gained a `cvAssetId` meanwhile, or the update never went through: nothing points at the PDF you
   just uploaded, so `delete_asset` it right away (never `delete`) and move on to the next job. If that delete
   fails too, `update` the doc with `cvDeleteAssetId: <the new asset id>` so the clean-up list of a later run
   removes it.

Never apply, submit forms, email anyone, or change profile/cv.

## 4. Notify

If at least one CV was made or skipped, send ONE push notification with the summary in `<routine_summary>` tags:
"N tailored CVs ready on your Job Swipe board", one line per job (Company — Role — main fit risk, or "skipped:
posting closed"), and the board URL ("under ♥, Open CV"). Only expirations happened → send nothing. If every build
failed, send a short notification saying what broke.
