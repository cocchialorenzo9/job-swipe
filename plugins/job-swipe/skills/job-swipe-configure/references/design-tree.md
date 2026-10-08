# Job Swipe design tree

Branches and their order. `after:` = prerequisites (a node joins the frontier once these are settled).
"Default" = what to recommend when their material gives you no better answer. Skip any node their material
already settles: confirm it instead of asking.

## A · Material (round 1, always first)

- **A1 Existing CV (required).** Ask them to attach it (PDF or Word). If they truly have none: ask for their
  LinkedIn profile as PDF (LinkedIn → their profile → More → Save to PDF), or build from the interview in branch B.
- **A2 Extra material (optional, same round).** LinkedIn PDF, portfolio / GitHub / personal site links,
  old cover letters, performance reviews, project write-ups, a job posting they'd love. More material = fewer
  questions.
- Then: read everything (WebFetch public links). Build a first draft of the master CV in your head, and list
  what's missing or vague.

## B · CV facts (deep dive; after: A)

Goal: enough true detail for strong "Accomplished X, as measured by Y, by doing Z" bullets.

- **B1 Confirm the skeleton**: roles (title, company, place, dates), education, as extracted. "Yes if right."
- **B2 Per role, newest first** (one round can cover 1–2 roles): the 2–3 achievements they're proudest of;
  for each, the number behind it (money, %, time saved, users, size, rank) and what they personally did; team size
  and who they worked with; main tools. Example answers help: "e.g. 'cut report time from 2 days to 1 hour'".
  Older or less relevant roles: one achievement is enough.
- **B3 Projects** (side, academic, open source, volunteering): name, what it does, their part, outcome, link.
- **B4 Education details** worth showing: grade (only if strong), thesis, relevant courses (mostly for juniors),
  exchanges, awards.
- **B5 Skills**: confirm the list. Ask "Which of these would you NOT want to be grilled on in an interview?" →
  those go to `never_list`. Ask for missing tools they use daily.
- **B6 Extras**: certificates (with year), languages with honest level (CEFR if they know it), publications,
  awards, volunteering.
- **B7 Contact line**: phone, email, city (city + country, never full address), LinkedIn, GitHub / website.
- **B8 Gaps or career changes** (only if the timeline shows one): how they want to present it. Their call.

## C · What jobs (after: A; can run in parallel with B)

- **C1 Roles**: job titles they want, in order; close variants worth searching. Default: from their last 2 roles
  and stated goal.
- **C2 Level**: how far a step up is OK (e.g. "Senior yes, Lead/Head of no"). Default: their level and one step up.
- **C3 Where**: city / remote / hybrid. after C3 = "open to moving": **C3b** where to, and on what condition
  (only for top roles? salary?).
- **C4 Work languages** and level. Default: skip jobs that need a language above their level.
- **C5 Companies**: size, industry, mission they like; companies to skip (incl. ones that rejected them).
- **C6 Must-haves**: salary floor (optional), visa sponsorship, max office days, contract type.
- **C7 Deal-breakers.**
- **C8 Pickiness**: lots of options / only good matches / only exceptional. Default: "only good matches".

## D · Rhythm (after: C8)

- **D1 How often to search**: Default twice a week (Mon + Thu), fits Pro usage limits. Every weekday if they are
  actively hunting and on a bigger plan; weekly if just curious.
- **D2 What time**: Default early morning in their time zone, so cards are ready with breakfast.
- **D3 Tailored CVs on?** Default yes.
- **D4 (after D3 = yes) CV time**: Default weekdays ~17:50 their time, so CVs are ready in the evening.
- **D5 Cards per run** follows pickiness (open 12, good matches 8, exceptional 4). Confirm or change.

## E · CV look and feel (after: D3 = yes, and B1)

Ask in two rounds at most, then prove it with a real sample (E-proto).

- **E1 CV language**: Default the language of the jobs they target (usually English).
- **E2 Spelling and date style**: Default US or UK spelling to match the target market; "Mar 2023 – Present".
- **E3 Length**: Default one page (two only with 10+ years of relevant experience).
- **E4 Font**: classic (LaTeX look, Latin Modern) · charter (warm, very readable) · palatino (elegant) ·
  sans (clean, Helvetica-like). Default: classic for technical/academic fields, sans for design/business.
- **E5 Colour**: all black, or one accent colour for links (and optionally headings). Default: dark blue links,
  black headings.
- **E6 Name style**: CAPITALS or as written. Default: capitals.
- **E7 Line under the name** (headline like "Product Manager | B2B SaaS"): Default yes, tailored per job.
- **E8 Summary at the top**: Default yes for career changers and 5+ years; optional otherwise.
- **E9 Section order**: Default Summary → Experience → Education → Skills (+ extras).
  Students / new graduates: Education first, then Projects.
- **E10 Extra sections**: which of Projects, Volunteering, Publications, Awards to include; bullets or one line
  each.
- **E11 Photo**: not supported, on purpose — many application systems strip or mangle photos, and in many
  countries a photo can introduce bias. If they insist, say so plainly and note it; don't fake it.
- **E-proto**: build a sample CV from their real facts, in the agreed style, aimed at their #1 target role
  (`build.py`). Send it to them (see SKILL.md, E-proto). One round: "Shall we keep this look?" plus 2–4 specific questions about what
  you see (density, colour, order, wording of the top bullets). Iterate up to 3 times.

## F · Angles (after: C1 and B2)

- **F1 Tracks**: 1–3 angles for different job types (e.g. "product" vs "engineering"), each with its headline,
  skill order, and which achievements go first. Default: one track per distinct role family in C1.
- **F2 Never stretch**: confirm the rule "the CV only ever contains things you told me or your CV shows". Yes.

## G · Wrap-up decisions (last round)

- **G1 First batch now?** Default yes (about 10 minutes).
- **G2 Anything we missed?** Open question.
