# Board spec

**Board spec version: 0.4.0.** This file describes a Job Swipe board completely: what it shows, what it looks like,
what it stores and how it behaves. `/job-swipe-configure` builds each person's board from it. The screenshots in
`board-screens/` show what a correct build looks like (phone width, 390 px). When this text and a screenshot
disagree, this text is right.

## How to build a board

1. Load the `artifact-capabilities` skill. It gives the exact calls for the page runtime (`db` storage and
   `downloads`). Use those calls; this spec only says which operations to do.
2. Write the board as **one HTML file** named `job-swipe.html` in the working directory: inline style and inline
   script, no build step, no frameworks, no external file except the two pdf.js files listed under
   [CV viewer](#cv-viewer).
3. Put `Board spec version: 0.4.0` (this file's version) into the page as the value shown in the preferences
   screen's "Board version" row.
4. Go through the [acceptance checklist](#acceptance-checklist). Fix every item that fails before you publish.
5. Look at your build next to the screenshots in `board-screens/`, in light and dark. Same layout, spacing,
   colours and text. Small differences in font rendering are fine, missing or moved parts are not.
6. Publish with the Artifact tool: `icon` "briefcase", `description` "My job feed: swipe right on jobs I like.",
   `capabilities` `{"db": {}, "assets": {}, "downloads": true}`.

## Safety rules (always)

Job fields were copied from web pages written by strangers. The board treats every stored value as plain text.

- Every stored value is inserted as text, never as markup. If you build markup from strings, escape `&`, `<`,
  `>`, `"` and `'` in every value, including ids used inside attributes.
- A link is only made from a value that starts with `http://` or `https://` (case-insensitive). Anything else
  shows no link. Every link opens in a new tab with `rel="noopener"`.
- No requests except: the board's own storage, its stored files (a job's `cvUrl`, or `/_blob/` + the URL-encoded
  `cvAssetId`), and the two pinned pdf.js files with their integrity hashes.
- No `eval`, no dynamic script from data, no inline event-handler attributes built from data.

## Data

Read and write through the `db` capability. Two collections.

**`profile` / doc `me`** (read once at start):

| Field | Meaning |
|---|---|
| `name` | Full name; the board greets with the first word |
| `brief` | Search brief text, editable in preferences |
| `briefUpdatedAt` | ISO time of the last brief save |
| `searchSchedule` | Human text, e.g. "Monday and Thursday mornings" |
| `cvEnabled` | Whether tailored CVs are on |
| `cvSchedule` | Human text for the CV run |
| `timezone` | IANA time zone |
| `askWhyAfterSwipe` | `false` turns off the "why?" strip; missing means on |

The board writes only `brief`, `briefUpdatedAt` and `askWhyAfterSwipe` to `profile/me`. To write, read the doc,
then update it if it exists, otherwise create it with just these fields.

**`jobs` / one doc per job:**

| Field | Meaning |
|---|---|
| `status` | `pending`, `liked`, `applied` or `disliked` |
| `company`, `title`, `location` | Text |
| `remote` | `true` adds " · Remote" after the location |
| `postedDate`, `addedDate` | Text dates |
| `blurb` | A few sentences about the role |
| `matchReason` | Why it matched; optional |
| `tags` | List of short texts; ignore if not a list |
| `url` | The posting |
| `swipedAt`, `appliedAt` | ISO times the board sets |
| `note` | The person's own "why", up to 140 characters |
| `cvAssetId`, `cvUrl` | The tailored CV file; `cvUrl` wins when both exist |
| `cvFileName`, `cvCreatedAt`, `cvNote` | About the CV |
| `cvStatus` | `created`, `expired`, `removed` or `skipped` |

## Look

### Colour tokens

Define these once and use only them. Dark values apply when the system is dark, unless the page root has
`data-theme="light"`; `data-theme="dark"` forces dark. Also set `color-scheme: dark` in dark mode.

| Token | Light | Dark | Used for |
|---|---|---|---|
| bg | `#f6f5f3` | `#171615` | Page background |
| card | `#ffffff` | `#232220` | Cards, buttons, boxes |
| text | `#1c1b1a` | `#f2f0ec` | Main text |
| sub | `#6b6864` | `#a19d97` | Secondary text |
| border | `#e4e1dc` | `#37352f` | All 1 px borders |
| accent | `#c65d3b` | same | Company names, primary buttons, links, focus rings |
| like | `#2f9e60` | same | Like button, "Interested" stamp, badge, restore buttons |
| pass | `#c14848` | same | Pass button, "Pass" stamp, pass buttons |
| chip-bg | `#f0ede8` | `#2c2a27` | Tags, quiet buttons, tab track, note boxes |
| shadow | `0 10px 30px -12px` black at 25% | same at 60% | Cards |
| cv-bg | `#eaf4ee` | `#1f2e25` | "CV ready" row |
| cv-text | `#23734a` | `#7fd1a2` | "CV ready" row text and Download button |

### Type and spacing

- Font: the system UI stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`). Buttons and
  inputs inherit it.
- Page: padding 24 px top, 16 px sides, 48 px bottom; content column max 460 px wide, centred.
- Every tappable control is at least 44 px tall, except the small text buttons named below.
- Focus: a 2 px accent outline, 2 px offset, on every button, link and tab when focused by keyboard.
- Disabled buttons: 40–60% opacity, default cursor.

| Element | Size and weight | Colour | Other |
|---|---|---|---|
| Title ("Job Swipe · Alex") | 19 px bold | text | Letter spacing −0.01em |
| Subline under the title | 13 px, line height 1.45 | sub | 20 px below |
| Company | 13 px semibold | accent | 4 px below |
| Job title on the swipe card | 20 px bold, line height 1.25 | text | 8 px below |
| Job title on list cards | 16 px bold | text | 6 px below |
| Meta line (place · Remote · date) | 13 px | sub | 14 px below (12 on list cards) |
| Blurb | 14 px, line height 1.5 | text | Scrolls inside the card if long |
| "Why it matched" box | 12.5 px | sub, label bold in text | chip-bg, radius 10, padding 10×12 |
| Tag | 12 px | sub on chip-bg | Pill, padding 4×9, 6 px gaps |
| Counts line ("2 to review") | 12 px, number bold in text | sub | 18 px below |
| Stats rows | 12.5 px | sub, numbers bold | Top border, 14 px padding above |

### Shapes

| Element | Shape |
|---|---|
| Swipe card | Radius 20, 1 px border, shadow, padding 22; fills a 480 px tall stage |
| List cards (tabs) | Radius 16, 1 px border, shadow, padding 16, 12 px apart |
| Preference boxes | Radius 16, 1 px border, padding 16, 14 px apart |
| ♥ count pill | Fully round, 1 px border, card background, 44 px tall, padding 8×12, 12.5 px semibold |
| ⚙ button | A 44 × 44 px circle (no padding), 1 px border, card background, the gear 20 px and centred; the same height as the ♥ pill |
| Like / pass buttons | 56 px circles, 1 px border, card background, soft shadow, 22 px symbol in like / pass colour, 16 px apart, centred |
| Ordinary buttons and inputs | Radius 10 |
| Tabs | A chip-bg track, fully round, padding 3; the selected tab has card background, text colour and a small shadow |

## Screens

The board has one column and three views: **Swipe** (start), **Saved jobs** and **Preferences**. Only one shows at
a time; switching scrolls to the top. A full-screen **CV viewer** opens on top of Saved jobs.

### Top bar (every view)

- Left: the title "Job Swipe · <first name>" ("Job Swipe" without a name). Under it the subline:
  "Right = interested, left = pass. New jobs arrive <searchSchedule, or 'at the next search'>." plus, when CVs are
  on, " Liked jobs get a tailored CV <cvSchedule, or 'at the next CV run'>."
- Right, side by side with 8 px between: the round ⚙ button (label "Preferences", tooltip "What I'm looking for")
  and a ♥ pill with a green badge holding the number of liked jobs (tooltip "Jobs you liked").

### Swipe view — `swipe-card-*.png`, `swipe-why-strip-light.png`, `swipe-empty-light.png`

From top to bottom:
1. Counts line: "<n> to review" on the left; on the right a small accent text button "↶ Undo", hidden until the
   first swipe.
2. The stage with the top pending job's card:
   - Company ("Unknown company" if missing), title ("Untitled role"), meta line, blurb.
   - "**Why it matched:** …" box, only when `matchReason` is set.
   - Tags.
   - Footer, space between: "✓ Already applied" (chip-bg button, 1 px border, tooltip "You applied to this job
     elsewhere") on the left; "View full posting ↗" (accent button, white bold text) on the right, only with a
     valid link.
   - Two stamps, hidden until dragging: "INTERESTED" top right in like colour, rotated −12°; "PASS" top left in
     pass colour, rotated 12°. 22 px, weight 800, 3 px border, radius 10.
3. The ✕ and ♥ round buttons (labels "Not interested" and "Interested").
4. The note row: a full-width input "Why? (optional)" (max 140), and under it 12 px sub text "Saved with your
   swipe. The next search reads it."
5. The "why?" strip, in place of the note row, after a swipe (see behaviour).
6. Stats: rows "Interested", "Applied", "Passed" with counts.

Empty states replace the card and hide the buttons and note row, centred in sub colour with a 34 px 🎉 above:
- No pending jobs: "You're all caught up." / "New matches arrive <searchSchedule or 'at the next search'>."
- While starting: "Loading…"
- Storage unavailable: "Can't reach this board's storage in this view." / "Open it from your Claude account."
- Not set up (no `brief` and no `name`): "This board isn't set up yet." / "Ask Claude: “configure Job Swipe”."

### Saved jobs — `tab-interested-*.png`, `tab-applied-light.png`, `tab-passed-light.png`

1. Header row: "← Back" (accent text button) and a 16 px heading: "Jobs you're interested in", "Jobs you applied
   to" or "Jobs you passed on", following the tab.
2. Three tabs: "♥ Interested", "✓ Applied", "✕ Passed". Interested is selected when the view opens.
3. The list, newest first (Interested and Passed by `swipedAt`, Applied by `appliedAt`; if ordering fails, load
   unordered). While loading: "Loading…".

Each list card shows company, title, and a meta line: place, " · Remote", and on Applied " · applied <day>", on
Passed " · passed <day>". Days are short local dates like "Oct 22". Then, in this order:

**CV row** (Interested always; Applied only when there is a CV or a `cvStatus`; never on Passed). Chip-bg box,
radius 10, 12.5 px:
- CV file present: cv-bg box, cv-text colour: "**Tailored CV ready** · <day of cvCreatedAt>", then "Open CV"
  (bold text button) and "⤓ Download" (small cv-text button with card-coloured text, radius 8). Under the box,
  `cvNote` in 12 px sub, if any.
- `expired`: "CV deleted after 7 days (made <day>)".
- `removed`: "CV deleted when CVs were turned off".
- `skipped`: "No CV made: <cvNote>" ("No CV made" without a note).
- Nothing yet and CVs on: "Tailored CV arrives <cvSchedule or 'at the next CV run'>". CVs off: no row.

**Note box**:
- With a note: chip-bg box "**Your note:** <note>" and a ✎ button on the right (label "Edit note").
- Without: a dashed-border box "No note yet. Tap to add one."
- Either one opens an edit row below: an input (prefilled, max 140, placeholder "Why? (helps the next search)")
  and a "Save" button.

**Actions** in one row, the primary action always on the right, filling the remaining width:
- Interested: "Mark applied" (chip-bg, 1 px border), "Pass" (pass-coloured border and text, transparent), then
  "Apply ↗" (accent). "Pass" opens a row with an input "Optional: why?" and a "Confirm pass" button in pass colour.
- Applied: "♥ Move to interested" (like-coloured border and text), then "View posting ↗".
- Passed: "♥ Move to interested", then "View posting ↗".
- Without a valid link the primary action is a greyed "No link saved" (chip-bg, sub text).

Empty tabs, centred, 34 px symbol above:
- Interested ♥: "Nothing here yet." / "Swipe right (or tap ♥) on a card to save it."
- Applied ✓: "No applied jobs yet." / "Tap “✓ Already applied” on a card, or “Mark applied” on a job you liked."
- Passed ✕: "No passed jobs." / "Jobs you swipe left on show up here, in case you change your mind."

### Preferences — `preferences-light.png`

"← Back" and the heading "What I'm looking for", then three boxes:
1. **Search brief**: text "The search reads this every time it runs. Change anything in your own words: roles,
   cities, salary, deal-breakers, companies to avoid." A textarea (at least 260 px tall, page background, resizable
   vertically) with the brief, placeholder "Describe the jobs you want: roles, cities, remote or not, salary,
   deal-breakers…". Below: an accent "Save" button (disabled until the text changes) and a status text: "Last
   saved <day>" when known.
2. **Swipe notes**: text "A short "why" is the strongest hint for the next search. You can always type one before
   you swipe." and a checkbox "Ask "why?" after each swipe" (20 px, accent colour), checked unless
   `askWhyAfterSwipe` is `false`.
3. **Schedule**: rows with the label left in sub and the value right in bold text: "New jobs" (searchSchedule or
   "not scheduled"), "Tailored CVs" (cvSchedule, "on" or "off"), "Time zone" (or "—"), "Board version" (this
   spec's version). Then: "To change the schedule or your CV details, ask Claude: “configure Job Swipe”."

### CV viewer — `cv-viewer-light.png`

A full-screen layer, black at 80% behind, as a modal dialog labelled "Tailored CV":
- Top bar (card background, bottom border): the file name (13 px semibold, cut with an ellipsis), an accent
  "Save PDF" button and a "Close" button.
- A notice bar, hidden unless the simple preview is used: "Showing a simple preview on this device." and an
  "Open full PDF" text button.
- A status line (white, 13 px, centred) and the pages: each page a white canvas, full width up to 820 px, 12 px
  apart, with a shadow, labelled "CV page <n>".

The pages are drawn with pdf.js **6.4.299** from cdnjs, loaded with these exact files and integrity hashes, and
never from anywhere else:

| File | URL | Integrity |
|---|---|---|
| Library (module script) | `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/6.4.299/pdf.min.mjs` | `sha384-QCvhu/UPp22U/TNLVbQNONL82ES2yY717GAiqP9VVu37Y7+m9VPKvadGx9XlFvcp` |
| Worker | `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/6.4.299/pdf.worker.min.mjs` | `sha384-NfW/OTMWezITv4oaALvfH7MFLwzPxEvpySmDpoALa1mtTY8MC200l0ZNFD+SOlrM` |

Load the library as a module script with the integrity hash and anonymous CORS. Fetch the worker with its
integrity hash, turn it into a local blob URL, and use that as the worker source. Keep the library once loaded;
retry only a failed load (with a different URL fragment, so the browser doesn't reuse the failed result).

## Behaviour

### Start

1. Show "Loading…". Ask for the `db` capability. If that fails, show the storage-unavailable empty state and stop.
2. Read `profile/me` (missing counts as empty). Fill the top bar.
3. Not set up → the not-set-up empty state. Otherwise load pending jobs: status `pending`, newest `addedDate`
   first, at most 100 (if ordering fails, load unordered). Show the first one.
4. Load the stats: counts of `liked`, `applied` and `disliked` (at most 1000 each). The ♥ badge shows the liked
   count. Reload stats after every status change.

A card that fails to render is skipped, and the next one is shown.

### Swiping

1. Drag the card with a pointer (not when the drag starts on a link or button). The card follows the pointer
   sideways and rotates by the distance ÷ 18 degrees. The "Interested" stamp fades in to the right and "Pass" to
   the left, fully visible at 80 px.
2. Let go past 110 px right → like; past 110 px left → pass; otherwise the card springs back and the stamps fade.
3. The ♥ button or the right arrow key likes; ✕ or the left arrow key passes; "✓ Already applied" marks the job
   applied. Arrow keys work only in the swipe view, with a card shown, and not while typing in a field.
4. On a swipe: the card flies 520 px out in its direction, rotating 20°, fading out (0.35 s ease). Write to the
   job: `status` (`liked`, `disliked` or `applied`), `swipedAt` now, `appliedAt` now when applied, and `note`
   when the note input has text. Clear the note input at once so the next card starts empty. After 220 ms show the
   next card.
5. Remember the swipe for undo and show "↶ Undo". Undo writes the job's earlier data back in full, puts it on top
   of the pile, hides "Undo" and the "why?" strip. Only the last swipe can be undone.
6. Enter in the note input never submits or swipes.

### The "why?" strip — `swipe-why-strip-light.png`

1. After a swipe without a note, when asking is on: a bordered box (card background, radius 14, padding 12) with
   a head line "**♥ Interested** · <job title>" ("✕ Passed" or "✓ Applied" to match), an input "Why? (optional,
   helps the next search)" (max 140) with a "Save" button, and two quiet text buttons "Not now" and "Don't ask
   again". The note row is hidden meanwhile.
2. After a swipe with a note: the box shows "Note saved: <note>" instead, and hides after 4 seconds.
3. Save (or Enter) writes `note` to that job and shows "Note saved: <note>" for 4 seconds. An empty answer just
   closes the strip. If the write fails: "Couldn't save the note. Try again from ♥."
4. An answer typed but not saved still counts when the next swipe happens.
5. "Not now" closes it. "Don't ask again" closes it and writes `askWhyAfterSwipe: false`.
6. Asking off and no note: no strip.

### Saved jobs

1. ♥ opens Saved jobs on the Interested tab. "← Back" returns to Swipe.
2. Changing tabs reloads the list. A list that finishes loading after the person switched tabs is thrown away.
3. Button actions show a short busy label and disable the button, write, then reload the list and the stats:
   - "Mark applied" ("Marking…"): `status: applied`, `appliedAt` now.
   - "Confirm pass" ("Passing…"): `status: disliked`, `swipedAt` now, and `note` if typed.
   - "♥ Move to interested" on Passed ("Moving…"): `status: liked`, `swipedAt` now, `note` cleared (it explained a
     "no").
   - "♥ Move to interested" on Applied ("Moving…"): `status: liked`, `appliedAt` cleared.
   - Note "Save" ("Saving…"): `note` set to the trimmed text.
4. Opening an edit or pass row moves the focus into its input; tapping the opener again closes it.

### CV viewer

1. "Open CV" opens the viewer: focus moves to "Close", the page behind becomes inert and stops scrolling, the
   status says "Opening your CV…", and after 3 seconds "Opening your CV… Still working, this can take a few
   seconds."
2. Fetch the file. 404, 410 or an empty file → hide "Save PDF" and say "This CV isn't available any more. It may
   have been deleted after 7 days. Ask for a new one by liking the job again." Any other failure → "Couldn't open
   this CV right now. Check your connection and try again." Never call a network error a deletion.
3. With the file: enable "Save PDF" and draw every page with pdf.js at a scale of device pixel ratio × 1.6 (at most
   3), with a 15-second limit.
4. If pdf.js can't load, fails its hash, times out or fails to draw: show the simple preview instead, the PDF in
   an iframe titled "CV preview" (at least 70% of the screen tall), plus the notice bar. "Open full PDF" opens the
   PDF in a new tab; if no tab opens: "This device didn't open a new tab. Use Save PDF instead."
5. Closing (Close, Escape, or a tap on the dark background) stops any drawing, discards results that arrive late,
   frees the file, and returns focus to the "Open CV" button.
6. While open, Tab and Shift+Tab cycle only through the viewer's visible controls.

### Saving a CV

1. "Save PDF" in the viewer and "⤓ Download" on a card save the file named by `cvFileName` (or "CV_<company>.pdf";
   add ".pdf" if missing).
2. Use the `downloads` capability. If the capability is missing, fall back to a normal browser download link.
3. Results on "⤓ Download": "Loading…" while fetching, then "Saved ✓", "CV not found" or "Save unavailable" for
   2.5 seconds, then back to "⤓ Download". Declined by the person: back to the label at once. "Save PDF" shows
   "Saved", or "Save unavailable" and stays disabled.

### Preferences

1. ⚙ opens Preferences, filled from the profile.
2. Editing the brief enables "Save" and clears the status. Save → "Saving…", then writes `brief` (trimmed) and
   `briefUpdatedAt` now, and says "Saved. The next search will use this." Failure: "Couldn't save. Try again." and
   "Save" is enabled again.
3. The checkbox writes `askWhyAfterSwipe` at once. If that fails, it flips back.

## Accessibility

- Every icon-only button has a label: "Preferences", "Not interested", "Interested", "Edit note".
- Tabs use tab roles with `aria-selected`; the tab group is labelled "Saved jobs".
- The "why?" result and the CV status line are polite live regions.
- Card stamps don't take pointer input. The page has `lang`, UTF-8 and a mobile viewport.

## Acceptance checklist

Check each item in the HTML before publishing:

- [ ] One file; the only external URLs are the two pdf.js files, with both integrity hashes exactly as above.
- [ ] Every stored value is escaped or inserted as text; links only from `http(s)` values, with `rel="noopener"`.
- [ ] All the colour tokens above, in light and in dark, with the `data-theme` overrides.
- [ ] Every text in quotes in this spec appears word for word.
- [ ] Swipe: drag thresholds 80 px (stamps) and 110 px (swipe), arrow keys, buttons, "Already applied", undo.
- [ ] A note typed before a swipe is saved with that job, and the input is empty for the next card.
- [ ] "Why?" strip: shows after a swipe, saves, "Not now", "Don't ask again", the 4-second close.
- [ ] Saved jobs: three tabs, each card type, every CV row state, note edit, pass with a reason, both "Move to
      interested" actions, the empty texts.
- [ ] CV viewer: pdf.js with the verified worker, the simple-preview fallback, the missing-file and network texts,
      the focus trap, Escape, and focus returning to "Open CV".
- [ ] Downloads through the `downloads` capability, with the browser-link fallback.
- [ ] Preferences: brief save, the "why?" checkbox, the schedule rows with "Board version" 0.4.0.
- [ ] Every control is at least 44 px tall except the small text buttons (Undo, Back, Open CV, tabs).
- [ ] Looks like the screenshots in `board-screens/` in light and dark at 390 px wide, with no sideways scrolling.
