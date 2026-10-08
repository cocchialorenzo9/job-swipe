---
name: configure
description: Configures a personal Job Swipe board — a swipeable job feed that a scheduled search fills with matching jobs, plus a tailored one-page CV for every liked job. Runs a thorough interview first (CV facts, target jobs, rhythm, CV look), then builds or updates everything. Use for "/job-swipe:configure", "set up Job Swipe", "configure Job Swipe", "change my Job Swipe settings", "update my CV details for Job Swipe", "search more/less often", "pause Job Swipe", or when given a Job Swipe board link to reconfigure.
---

# Job Swipe — configure

One skill for both first-time setup and later changes. You are talking to someone who probably does not code:
plain, warm, short messages. Never mention YAML, LaTeX, JSON, databases, cron, skills or plugins — say "your board",
"your search brief", "your CV details", "your schedule".

Files (paths relative to this SKILL.md):
- `references/grilling.md` — HOW to interview (rounds, question format, facts vs decisions). Read it first.
- `references/design-tree.md` — WHAT to cover, in which order, with recommended defaults.
- `references/brief-template.md` — the search brief format.
- `references/task-prompts.md` — the scheduled-task prompts.
- `../../references/board-data.md` — which tools touch the board, and how to handle a refused write.
- `../../board/job-swipe.html` — the board page.
- `../../.claude-plugin/plugin.json` — the kit's `version` (stamped as `kitVersion`).
- `../tailor-cvs/cv/` — CV builder (`build.py`), `examples/master_cv.example.yaml` (structure + rules for CV
  details, incl. `style`), `examples/job_spec.example.yaml`.

## 0. Detect the situation

1. Tools: you need the Artifact tool and the scheduled-task tools (`create_trigger`, `update_trigger`,
   `list_triggers`; load deferred tools with ToolSearch). Read and write board data as `../../references/board-data.md`
   says. Without scheduled tasks, say plainly
   this needs a paid Claude plan (Pro or higher) in the Claude app, and stop.
2. Find an existing board: a board URL in the request, or Artifact `list` → an artifact titled "Job Swipe".
   If found, `read_db` `get` profile/me and profile/cv.
   - **Board exists and is configured → Reconfigure mode** (section 6).
   - **Board exists but profile/me is empty**, or **no board → First-time mode** (sections 1–5). Reuse an empty
     existing board instead of publishing a new one.

## 1. Open the interview (first time)

Send one short message:
- What you'll build together, in 3 lines: their board, a search on their schedule, a tailored CV per liked job.
- How it works: "I'll ask in short rounds. Each question has my suggestion; 'yes' accepts it. You can answer by
  number. Say 'one at a time' if you prefer."
- Round 1 = design-tree branch A: **ask them to attach their current CV (required)** and any extra material
  (LinkedIn PDF, portfolio/GitHub links, project write-ups, a dream job posting).

Wait for the CV. Read every file and public link fully before the next round.

## 2. Grill until the frontier is empty

Follow `references/grilling.md` over the tree in `references/design-tree.md`:
- Front-load the CV deep dive (branch B): you want every role, project, education detail and the numbers behind
  achievements. Branch C (what jobs) can share rounds with B once A is done.
- Branch E (CV look) only if they want tailored CVs; finish it with **E-proto**: build a sample CV from their real
  facts in the agreed style (write `master_cv.yaml` + a small spec for their #1 target role, run
  `python3 ../tailor-cvs/cv/build.py master_cv.yaml spec.yaml cv_sample`; it must say `ATS text check: OK` and stay
  within the page limit), look at a preview yourself (`pdftoppm -r 70 -png`), send them the PDF (with your file-sharing tool, e.g. SendUserFile; if you have none, tell them where the PDF is saved so they can open it), and run
  one look-and-feel round on what they see. Iterate up to 3 times.

While grilling, keep two drafts up to date in your working directory:
- `brief.md` — the search brief (`references/brief-template.md`), in their language, only their facts and choices.
- `master_cv.yaml` — their CV details, exactly in the structure and under the rules of
  `../tailor-cvs/cv/examples/master_cv.example.yaml`, including `style` (from branch E), `tracks` (branch F) and
  `never_list`. Truth only: rewording into XYZ bullets is fine; new facts are not. Plain text, no LaTeX.

## 3. Shared understanding — confirm before building

When the frontier is empty, send ONE summary and wait for an explicit yes:
- **Jobs**: the brief in 5–8 bullets.
- **Rhythm**: when searches run, cards per run, CVs on/off and when.
- **CV**: look (font, colour, length, section order), angles/tracks, and a count like "5 roles, 14 achievements,
  9 with numbers"; anything you left out on purpose (never-list skills, unconfirmed numbers).
- **Open points**: anything still assumed. If there are any, they are questions — ask them first.
Ask: "Shall I build it like this?" Build nothing until they say yes. Changes → update drafts, re-summarise briefly.

## 4. Build

1. **Board** (skip if reusing an empty one): copy `../../board/job-swipe.html` into the working directory unchanged
   and publish it with the Artifact tool: `icon` "briefcase", `description` "My job feed: swipe right on jobs I
   like.", `capabilities` `{"db": {}, "assets": {}, "downloads": true}` (load the artifact-capabilities skill first
   if your tools ask you to). Keep the returned URL as BOARD_URL.
2. **Profile**: `write_db` `set` collection `profile`, doc `me`:
   `name, timezone (IANA), language (of the brief), brief (text of brief.md), pickiness ("open" | "selective" |
   "exceptional"), maxNewPerRun, searchSchedule (human text, e.g. "Monday and Thursday mornings"), cvEnabled,
   cvSchedule (human text, omit if off), learned ([]), configuredAt (ISO now), boardUrl, kitVersion (the `version` in `../../.claude-plugin/plugin.json`)`.
3. **CV details** (if CVs on): `write_db` `set` collection `profile`, doc `cv`:
   `{masterYaml: <full text of master_cv.yaml>, updatedAt: <ISO now>}`.
4. **Check**: `read_db` `get` profile/me — the brief must be there.
5. **Schedules** with `create_trigger` (their time zone as `CRON_TZ=<tz>`, minutes off the hour), prompts from
   `references/task-prompts.md` with BOARD_URL filled in:
   - "Job Swipe: find jobs" — e.g. twice a week at 7:47 → `CRON_TZ=<tz> 47 7 * * 1,4`; weekdays → `1-5`;
     weekly → `1`.
   - "Job Swipe: tailored CVs" (if on) — e.g. `CRON_TZ=<tz> 52 17 * * 1-5`. It exits at once on days with
     nothing new, so it costs little.
   Save the ids: `write_db` `update` profile/me with `searchTaskId`, `cvTaskId`.
   If a result's `permission_mode` is not "auto", tell them: "Open Scheduled tasks in Claude, open each Job Swipe
   task and turn on 'Automatically approve', otherwise it waits for you instead of running."
6. **First batch** (if they said yes in G1): follow `../find-jobs/SKILL.md` for BOARD_URL here and now (max 6
   cards, skip its notification step).

## 5. Wrap up (4–6 short lines)

- The board is in their Claude artifacts as "Job Swipe": pin it, and use the Claude phone app to swipe.
- Right = interested, left = not, ✓ = already applied; a short "why" note makes the next search smarter.
- ⚙ on the board shows their search brief, and they can edit it there any time.
- Liked jobs get a CV under ♥ ("Open CV") the next time the CV task runs (tell them when, from their CV
  schedule, e.g. "weekday evenings, so a job liked on Saturday gets its CV on Monday"); CVs are deleted after 7 days.
- Changed your mind? ♥ → "Passed" lists every job you swiped left on, with "Move to interested".
- Anything else: "configure Job Swipe" again.

## 6. Reconfigure mode

1. Read profile/me (and profile/cv). Show the current setup in 4–5 lines (jobs, rhythm, CV look, last configured).
2. If they already said what to change, grill only that branch of the tree (plus anything it unblocks).
   Otherwise ask one round: "What would you like to revisit? 1 jobs, 2 how often, 3 CV details (new job, new
   achievements), 4 CV look, 5 pause or stop, 6 a full re-interview".
3. Same rules: rounds, recommendations, facts are yours; confirm a short summary of the changes before applying.
4. Apply only what changed:
   - Brief → `update` profile/me `brief`, `briefUpdatedAt`.
   - Rhythm → `update_trigger` (ids from profile/me, else `list_triggers`), update `searchSchedule` / `cvSchedule`
     / `maxNewPerRun` / `pickiness`.
   - CV details or look → edit the YAML from profile/cv, rebuild a sample (E-proto) if the look changed,
     `set` profile/cv.
   - CVs on → build CV details (branches B, E, F) if missing, create the CV task, `cvEnabled: true`.
     CVs off → `update_trigger` enabled=false, `cvEnabled: false`.
   - Pause/stop → disable both tasks. Delete the board only if they explicitly ask, after saying it can't be
     undone.
5. Confirm in one line what changed.
