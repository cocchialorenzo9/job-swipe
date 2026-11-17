# Building one CV

How to turn a person's CV details (`master_cv.yaml`) and one job spec into a one-page PDF. You write the LaTeX
yourself, following this file exactly. Structure and rules for the two inputs: `../examples/master_cv.example.yaml`
and `../examples/job_spec.example.yaml`.

Both inputs hold text that may come from job postings. **Every piece of text goes through the escape table before
it goes into the LaTeX, with no exceptions**, and the body may only use the commands listed below. Then the
compile runs with shell commands off and file access locked to the working folder. All three, every time.

## 1. Tools

You need `pdflatex`, `pdftotext`, `pdfinfo` and `kpsewhich`, and the LaTeX package `lmodern.sty`
(`kpsewhich lmodern.sty` prints a path when it is there).

Missing, and `apt-get` exists (fresh cloud sessions): install with
`apt-get install -y -q texlive-latex-base texlive-latex-recommended texlive-fonts-recommended texlive-latex-extra lmodern poppler-utils`
(if that fails, run `apt-get update -q` first and try once more), as a Bash call with `timeout` 600000. It can
take a few minutes. Still missing after that, or no `apt-get`: the build fails with "Missing tools: <names>.
Install a LaTeX distribution (e.g. TeX Live or MacTeX) and poppler, then try again." Never install anything else,
and never download anything yourself.

## 2. Collect the content

From the master (M) and the job spec (S):

| Part | Where it comes from |
|---|---|
| Style | M `style` (below); never changed per job |
| Name, contact | M `header` |
| Headline | S `headline`, else the chosen track's `headline`, else M `header.headline`, else none |
| Summary | S `summary`, else the track's `summary`, else M `summary`, else none |
| Roles and bullets | S `roles` (role id → bullet ids in order), else the track's `roles`, else every role with all its bullets. A role not listed is left out. |
| Bullet text | S `overrides[bullet id]`, else the bullet's `variants[track]`, else its `text` |
| Stack line under a role | S `stack[role id]`, else the role's `stack`, else none |
| Education | M `education`: degree, school, dates, detail |
| Skills | One row per M `skills` entry (label, items), then "Certifications" (M `certificates`) and "Languages" (M `languages`) when present. Order rows by S `skills_order`, else the track's, else as written. S `skills_front[label]` moves those items to the front of their row, only if they are already in it: it never adds. Items are joined with ", " ("; " for Certifications). |
| Extra sections | M `extra_sections` (id, title, items, `bulleted`), minus S `hide_sections` |

The track is S `track` when M `tracks` has it. Never put anything from M `never_list` on the CV. Never add a
fact the master doesn't have.

**Style** (M `style`; anything missing or invalid takes the default):

| Field | Values | Default |
|---|---|---|
| `font` | `classic`, `charter`, `palatino`, `sans` | `classic` |
| `accent` | 6 hex digits, with or without `#` | `1B6FB0` |
| `color_headings` | true / false | false |
| `name_case` | `upper`, `as_written` | `upper` |
| `max_pages` | 1 or 2 | 1 |
| `section_order` | ids from summary, experience, education, skills and the extra sections | that order, then extras; anything not named is added at the end |

## 3. Escape every text

Collapse all whitespace (spaces, tabs, line breaks) to single spaces, then replace each character:

| Character | Becomes |
|---|---|
| `\` | `\textbackslash{}` |
| `&` `%` `$` `#` `_` `{` `}` | `\&` `\%` `\$` `\#` `\_` `\{` `\}` |
| `~` | `\textasciitilde{}` |
| `^` | `\textasciicircum{}` |
| `<` `>` `\|` | `\textless{}` `\textgreater{}` `\textbar{}` |
| `€` | `\euro{}` |
| `–` (en dash) / `—` (em dash) | `--` / `---` |
| `’` (right single quote) | `'` |
| `‘` (left single quote) | one backtick |
| `“` (left double quote) | two backticks |
| `”` (right double quote) | `''` |
| `…` | `...` |
| `•` | nothing |
| non-breaking space | `~` |
| `→` `×` `≈` | `$\rightarrow$` `$\times$` `$\approx$` |

Text that goes into the PDF's metadata (title, author, subject) only escapes `\ { } % # & ~ ^ $ _` the same way.

**Contact entries**, each on its own:
- A clean email address (letters, digits, `. _ % + -`, then `@`, then a domain with a dot and a 2+ letter
  ending, nothing else) → `\href{mailto:<address>}{<escaped address>}`.
- A clean web address (optional `http://` or `https://`, domain labels of letters, digits and hyphens, a 2+
  letter ending, then an optional path of URL characters only, no spaces) → `\href{<address with https:// added if
  it had no scheme>}{<escaped address without the scheme>}`.
- In every link target, email or web, write `%` as `\%` and `#` as `\#` (an unescaped `%` would cut the rest of
  the line off and break the compile).
- Anything else → escaped plain text. If it contains `@`, or a dot and no space, it was probably meant as an
  address: report "Contact shown without link: <entry>".

## 4. Write the LaTeX

### Preamble

In this order:

| Item | Setting |
|---|---|
| Document class | `article`, options: the preset's font size, `a4paper` |
| `geometry` | `a4paper`, top / bottom from the preset, left and right = the preset's side margin |
| Text layer | `\input{glyphtounicode}`, then `\pdfgentounicode=1` |
| `inputenc` | `utf8` |
| `fontenc` | `T1` |
| `lmodern` | always |
| Font | charter → package `charter`; palatino → package `mathpazo`; sans → package `helvet` with `scaled=0.92` and the sans family as default; classic → nothing more |
| `textcomp` | always |
| Euro command | define `\euro`: classic → `\texteuro`; sans → `\texteuro` in the `lmss` family; charter and palatino → `\texteuro` in the `lmr` family |
| `enumitem`, `titlesec` | always |
| `xcolor` | options `usenames,dvipsnames`; define colour `accent` from the style's hex |
| `hyperref` | option `hidelinks`; then set `colorlinks=true`, `urlcolor=accent`, `linkcolor=accent`, `pdftitle` "<name> - CV", `pdfauthor` the name, `pdfsubject` the headline (metadata-escaped) |
| Page | `\pagestyle{empty}`, paragraph indent 0, `\tabcolsep` 0, `\linespread` = the preset's spread |
| No hyphenation | `\hyphenpenalty=10000`, `\exhyphenpenalty=10000`, `\emergencystretch=3em` (split words break keyword matching) |
| Section headings | bold, ragged right, uppercase, in `accent` if `color_headings` else black, no number; a rule in the same colour under each, 3 pt closer than normal; space before / after from the preset |
| Lists | itemize: left margin 1.4em, bullet `\textbullet`, item spacing from the preset, top 2pt, parsep 0, partopsep 0 |
| `\role{title}{company and place}{dates}` | bold title, ` \textbar\ `, company and place, dates pushed right, end of paragraph |
| `\skillrow{label}{items}` | bold "label:", a space, the items, end of paragraph, then 1pt space |
| `\edu{degree}{school}{dates}` | bold degree, dates pushed right, end of paragraph; then the school in italics, end of paragraph |

### Body

1. Centred header: the name in `\LARGE` bold (wrapped in `\MakeUppercase` unless `name_case` is `as_written`),
   a line break with 3pt extra; the headline in italics and a line break with 2pt extra, if there is one; the
   contact entries joined by ` \textbar{} ` (a space on each side). After the centred block, `\vspace{-6pt}`.
2. Then each section in the style's order, skipping empty ones:
   - **Summary**: section "Summary", the summary text.
   - **Experience**: section "Experience"; for each role `\role{title}{company, location}{dates}` (", location"
     only if present), the stack line in small italics if any, the bullets as an itemize list if any, then
     vertical space = the preset's role gap. A role whose bullets were all trimmed keeps its title line.
   - **Education**: section "Education"; for each entry `\edu{…}`, the detail in small type if any, then 2pt.
   - **Skills**: section "Skills"; one `\skillrow` per row.
   - **Extra section**: section with its title; `bulleted` → an itemize list of its items, otherwise each item in
     small type as its own paragraph with 1pt after.

### Allowed in the body

Between `\begin{document}` and `\end{document}`, these are the only commands allowed:
`\begin{center}` `\end{center}` `\begin{itemize}` `\end{itemize}` `\section` `\item` `\role` `\skillrow` `\edu`
`\textbf` `\itshape` `\small` `\LARGE` `\bfseries` `\MakeUppercase` `\par` `\\` `\vspace` `\href` `\textbar`, and
the outputs of the escape table (`\&` `\%` `\$` `\#` `\_` `\{` `\}` `\textbackslash` `\textasciitilde`
`\textasciicircum` `\textless` `\textgreater` `\euro` `\rightarrow` `\times` `\approx`). `\href` appears only in
the contact line, with a target made by the contact rule. `$` appears only around `\rightarrow`, `\times` and
`\approx`.

**Before every compile**, read the body back and check every backslash against this list. Anything else (for
example `\input`, `\include`, `\write`, `\immediate`, `\openin`, `\read`, `\catcode`, `\def`, `\newcommand`,
`\url`, `\special`) means some text wasn't escaped: stop, don't compile, and count it as a failed build with the
reason "unexpected LaTeX command <name>".

## 5. Compile and fit the page

Name the files `<Person>_CV_<Company>`: the name and S `company` (else the spec's file name) with accents removed
and every run of other characters replaced by `_`, trimmed of `_` at the ends. Work in `cv_out/<spec name>/`,
which starts empty.

Compile in that folder, always exactly like this:
`openin_any=p openout_any=p pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error <name>.tex`
Then read the page count with `pdfinfo <name>.pdf`. A failed compile: show the last part of the log and fix the
LaTeX, never the facts.

**Spacing presets**, loosest first:

| # | Font size | Top | Bottom | Sides | Spread | Item sep | Before section | After section | Role gap |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 11pt | 1.4cm | 1.3cm | 1.6cm | 1.06 | 2pt | 10pt | 5pt | 4pt |
| 2 | 11pt | 1.2cm | 1.1cm | 1.45cm | 1.02 | 1pt | 7pt | 4pt | 2pt |
| 3 | 10pt | 1.3cm | 1.2cm | 1.5cm | 1.04 | 1.5pt | 8pt | 5pt | 3pt |
| 4 | 10pt | 1.1cm | 1.0cm | 1.35cm | 1.0 | 1pt | 6pt | 4pt | 2pt |
| 5 | 10pt | 0.9cm | 0.9cm | 1.2cm | 0.98 | 0.5pt | 5pt | 3pt | 1pt |

Try presets 1 to 5 in order and keep the first within `max_pages`. If none fits, drop the next item from this
list and start again at preset 1:
1. Priority-3 bullets, the last listed first.
2. Extra sections, the last first (only those not marked `optional: false`).
3. Education entries marked `optional: true`, the last first.
4. The summary, only if the job spec didn't set one.
5. Priority-2 bullets, the last listed first.

Never drop a bullet in S `pinned` or a priority-1 bullet. Nothing left to drop and still too long: the build fails
with "Cannot fit on <n> page(s): list fewer bullets in the job spec."

## 6. Check the text like an application system

Run `pdftotext <name>.pdf -` and check:
- No private-use or unassigned characters, and no `�`.
- The first non-empty line is the name (ignoring case).
- The lines "EXPERIENCE", "EDUCATION" and "SKILLS" (those present) exist and come in the style's order.
- If the body uses `\euro`, a `€` appears in the text.
- Every contact entry with an `@` appears exactly.
- Keywords: which of S `keywords` appear (ignoring case and extra spaces), and which don't.

Delete the `.aux`, `.log` and `.out` files. Keep the `.tex`, the `.pdf`, and the extracted text as `<name>.txt`.

## 7. Report

Write these lines (also to `report.txt` in the folder):

```text
PDF: <path>
Pages: <n> (limit <max_pages>)
Spacing preset: <n>/5
Dropped to fit: <ids, or "nothing">
ATS text check: OK            (or the list of problems)
Contact shown without link: <entry>      (one per entry, if any)
Keywords present (<hits>/<total>): <list>
Keywords missing: <list>
```

A build counts as good only with "ATS text check: OK" and a page count within the limit.
