---
name: find-jobs
description: Searches the web for new job openings that match a person's Job Swipe brief and swipe history, verifies them on the company's own site, and adds them as cards to their Job Swipe board. Use when a scheduled task says "Job Swipe: find new jobs", or someone asks to "find me jobs now", "refresh my Job Swipe board", or "run the job search".
---

# Job Swipe — find jobs

Input: the board URL (from the arguments or the prompt). If you have none, find the person's "Job Swipe" artifact
with Artifact `list`. When running on a schedule: never ask questions; make reasonable calls and finish.

Read `../../references/board-data.md` first: which tools touch the board, and how to handle a refused write.

Be efficient — most people run this on a Pro plan with usage limits. Aim for about 15–25 web searches per run and
stop searching once you have enough strong candidates for `maxNewPerRun`.

## 1. Load the profile

`read_db` `get` collection `profile`, doc `me`. You need: `brief` (the source of truth: the person wrote or
approved it), `pickiness`, `maxNewPerRun`, `language`, `timezone`, `learned` (patterns earlier runs noticed).
If the doc is missing or has no brief, send one push notification "Your Job Swipe board isn't set up yet: ask
Claude to 'configure Job Swipe'." and stop.

## 2. Learn from swipes

`read_db` `list` collection `jobs` with `query.limit` 1000 and an `out_dir` in your scratch folder; summarise
the files with a short script instead of reading them one by one.
- Build the "already seen" set: every doc id, and every company + title pair (any status).
- Liked / applied = good examples; disliked = bad examples. Notes (`note`) are the strongest signal.
- Note soft trends (seniority, company type, location, language, stack, industry). Trends nudge the search;
  they never override the brief. One or two swipes are not a trend.
- Tidy up: `pending` cards with `addedDate` older than 30 days → `update` to status `stale`.

## 3. Search

Turn the brief into 6–12 searches: role titles (and close variants) × places, plus 1–2 searches aimed at the kind
of company they like. Sources, best first:
- **hiring.cafe** through WebSearch (`site:hiring.cafe <role> <city>`). WebFetch on hiring.cafe is blocked: use the
  result snippets to find the company and role, then go to the company's own page.
- Company career pages and their applicant systems (Greenhouse, Lever, Ashby, Workday, Personio, SmartRecruiters).
- Good boards for the region, e.g. Europe: startup.jobs, welcometothejungle.com, englishjobs.de (Germany),
  berlinstartupjobs.com; US/global: ycombinator.com/jobs, wellfound.com, builtin.com; remote: weworkremotely.com,
  remoteok.com. LinkedIn/Indeed pages usually can't be read — use them only as leads.
- If an Agent tool is available, you may hand the searching to 1–2 subagents with the brief, the filters below
  and the "already seen" list; check their results yourself.

## 4. Filter

Keep a job only if ALL hold:
- Matches the brief's roles, level, places and languages, and breaks none of its must-haves / deal-breakers.
- Not in the "already seen" set (same id, or same company + very similar title) and not a company the brief says
  to skip.
- Passes the pickiness bar:
  - `open`: a reasonable match on role and place.
  - `selective`: strong on role, level and place; company is solid.
  - `exceptional`: worth seriously considering even for someone happy where they are — top company or standout
    startup, strong fit on every point. Zero results is a good outcome; never pad.
- Seniority: skip roles asking for far more experience than the person has (more than ~2 years above), unless the
  brief says otherwise.

## 5. Verify on the company's own site

- Open the posting on the company's site / applicant system and confirm it's live. Handy checks:
  Greenhouse `https://boards-api.greenhouse.io/v1/boards/<company>/jobs/<id>`;
  Lever `https://api.lever.co/v0/postings/<company>?mode=json`; an Ashby posting shows
  "<Title> @ <Company>" when live and just "Jobs" when closed.
- Store the company-site URL, not the board's.
- Can't verify: for `open`, keep it with the tag "Unverified"; for `selective` / `exceptional`, drop it.

## 6. Add the cards

- Doc id = first 20 hex characters of sha256(canonical URL: lower-case host, no tracking parameters like utm_*,
  gh_src, ref, source; no trailing slash). Compute it with a one-line script.
- Add at most `maxNewPerRun` cards, best first. One `write_db` `batch` with `set` ops (50 writes max per batch), collection `jobs`:
  ```
  title, company, location, url, source ("hiring.cafe" | "web"), remote (true/false),
  blurb (2–4 sentences: what the job is, team, stack/domain, anything notable like salary),
  matchReason (1–2 sentences: why it fits THIS person's brief — be concrete),
  tags (3–6 short tags: role family, city, Remote, Startup/Enterprise, industry, "Unverified" if so),
  postedDate (as shown, if known), addedDate (ISO now), status "pending"
  ```
- Write blurb, matchReason and tags in the profile's `language`.

## 7. Remember clear patterns

If you saw a clear, repeated pattern in the swipes (3+ consistent signals, or a note that states it), add one short
line to `profile/me.learned` (`get` profile/me fresh, then `write_db` `update` with the full new array and
`if_version`; keep at most 15 lines, drop the oldest, no duplicates). If the person edited the profile meanwhile,
follow `../../references/board-data.md`: re-read, rebuild the array from the fresh `learned`, write again. Never edit `brief` — it belongs to the person.

## 8. Notify

Only if you added at least one card: send ONE push notification (PushNotification tool) with the summary inside
`<routine_summary>` tags: first line "N new jobs on your Job Swipe board", then one line per job (Company — Title —
place — a few words on why), then the board URL. Added nothing: send nothing. If something broke (board unreachable,
every search failing), send a short notification saying what broke.

Never apply to jobs, fill in forms, or contact anyone.
