---
name: tailor-cvs
description: Builds a tailored, one-page, ATS-readable CV for each job a person liked on their Job Swipe board, using only the facts in their saved CV details, and attaches the PDFs to the board. Use when a scheduled task says "Job Swipe: make tailored CVs", or someone asks to "make my CVs now", "tailor my CV for the jobs I liked", or "make a CV for <company> from my board".
---

# Job Swipe — tailored CVs

Input: the board URL (from the arguments or the prompt; otherwise find the "Job Swipe" artifact with Artifact
`list`). On a schedule: never ask questions; make reasonable calls and finish.

Board data (the `profile` and `jobs` collections) is read and written with the Artifact tool's `read_db` /
`write_db` actions (`url` = board URL, `db_op` get/list/query/set/update/batch). Older apps expose the same
operations as a separate ArtifactData tool; load whichever exists with ToolSearch if deferred. Every
`update` / `set` on a doc you read passes its `version` as `if_version`.

The builder lives next to this file in `cv/`: `build.py` (renders in the person's chosen style, enforces the page limit, checks the text like an application system),
`template.tex.j2` (the look), `examples/` (a sample master CV with the rules, and a sample job spec).

## 0. Quick exit (do this first, it keeps empty days cheap)

1. `read_db` `query` collection `jobs` where `status == "liked"`.
2. **To build**: liked docs with no `cvAssetId` and no `cvStatus`, and `swipedAt` within the last 14 days.
3. **To expire**: any doc (any status) with `cvAssetId` and `cvCreatedAt` older than 7 days — query
   `status` `liked` and `applied`.
4. If both lists are empty: stop now. No notification.

## 1. Expire week-old CVs

For each doc to expire: Artifact `delete_asset` with `url` = board URL and `asset_id` = its `cvAssetId`. **Never
use Artifact `delete` here: it deletes the whole board.** If the asset is already gone, carry on. Then `get` the doc
and `update` it: `cvStatus: "expired"`, `cvExpiredAt` (ISO now), `cvUrl: ""`, `cvAssetId: ""`. Keep the rest.

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
d. Build: `python3 <this folder>/cv/build.py master_cv.yaml jobs/<spec>.yaml cv_out`.
   It must report `ATS text check: OK` and a page count within the limit (`style.max_pages`, default 1). Render once (`pdftoppm -r 70 -png <pdf> prev`) and look:
   no orphan one-word lines, nothing important dropped. Fix the spec, not the facts, and rebuild if needed.
e. Upload the PDF to the board: Artifact `upload_asset` with `url` = board URL and `file_path` = the PDF.
   Store the returned asset id as `cvAssetId` and its url as `cvUrl`, exactly as given.
f. `get` the doc again; if it gained a `cvAssetId` meanwhile, stop for this job. Otherwise `update` it:
   `cvStatus: "created"`, `cvAssetId`, `cvUrl`, `cvFileName` (the PDF's name), `cvCreatedAt` (ISO now),
   `cvNote` (≤ 200 characters, in the profile's `language`: the angle chosen + fit risks, e.g. posting keywords the
   CV could not truthfully cover, a language requirement, a big seniority gap).

Never apply, submit forms, email anyone, or change profile/cv.

## 4. Notify

If at least one CV was made or skipped, send ONE push notification with the summary in `<routine_summary>` tags:
"N tailored CVs ready on your Job Swipe board", one line per job (Company — Role — main fit risk, or "skipped:
posting closed"), and the board URL ("under ♥, Open CV"). Only expirations happened → send nothing. If every build
failed, send a short notification saying what broke.
