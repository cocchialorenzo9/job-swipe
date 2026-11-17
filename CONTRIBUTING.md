# Contributing

Thanks for helping. Job Swipe is small, but every change reaches people's job search while they sleep, so the bar
for merging is "safe for someone who never reads this repo".

## How the pieces fit

```
marketplace.json ─► plugins/job-swipe (installed in the Claude app)
                       ├─ skills/job-swipe-configure   interview, creates the board + scheduled tasks
                       ├─ skills/find-jobs             scheduled: search, verify, add cards
                       ├─ skills/tailor-cvs            scheduled: one CV per liked job (references/cv-build.md)
                       ├─ references/board-data.md     rules every skill follows (board writes, untrusted content)
                       └─ references/board-spec.md     the board's design; Claude builds each board from it

reference/ (never shipped)
                       ├─ board/job-swipe.html         the reference board: what the spec and its screenshots show
                       └─ cv/build.py                  the reference CV builder: what cv-build.md describes
```

The plugin folder ships only Markdown, text, JSON, YAML and images: the Claude plugin directory refuses code from
publishers that aren't Verified organizations (see `docs/adr/0001-markdown-only-plugin.md`). A test fails if any
other file type lands under `plugins/`. Code that helps build or check the plugin goes in `reference/` or `tests/`.

People reach the instructions only through the **plugin install**: the Claude app follows `main` and picks up a
change when `plugin.json`'s `version` changes. Nothing clones or downloads the instructions at run time (a
scheduled task without the plugin notifies and stops), so the directory's review covers everything that runs.

So **a merge to `main` reaches everyone at their next plugin update.**

## Skill text is code

Any change to a `SKILL.md` or a file under `references/` changes what an unattended agent does with someone's CV,
with auto-approve on. Review it like code:

- Does it keep the untrusted-content rules in `references/board-data.md` intact?
- Could it make the agent ask a question on a schedule (nobody is there to answer), loop, or use much more of the
  person's Claude usage?
- Could it lose data? Board writes go through `if_version`; `Artifact delete` is used on a board only by configure's "Delete
  everything", when the person explicitly asked.

## Checks to run

```bash
python3 -m unittest discover tests
```

The CV builder tests need LaTeX and poppler (`pdflatex`, `kpsewhich`, `pdftotext`, `pdfinfo`); without them those tests skip
locally (CI runs them with `REQUIRE_LATEX=1`, where a skip fails). They test the reference builder, which
`cv-build.md` describes: change both together. Build the example CV once by hand too:

```bash
python3 reference/cv/build.py plugins/job-swipe/skills/tailor-cvs/examples/master_cv.example.yaml plugins/job-swipe/skills/tailor-cvs/examples/job_spec.example.yaml cv_out
```

It must report `Pages: 1` and `ATS text check: OK`.

The board's CV viewer has browser tests (Chromium desktop, WebKit phone):

```bash
pip install -r tests/board/requirements.txt && python3 -m playwright install chromium webkit
python3 -m unittest tests.board.test_board_visual
```

Screenshots land in `tests/board/out/`. The spec's own screenshots come from
`python3 tests/board/capture_spec_screens.py`, which writes `plugins/job-swipe/references/board-screens/`. The repo checks (`tests/test_repo_consistency.py`) also download the pinned
pdf.js files and compare their hashes when `NETWORK=1` (always in CI).

## Trying a skill change safely

1. Fork the repo and push your branch.
2. In the Claude app: **Customize → Plugins → Add → Add marketplace → Add from a repository**, enter your fork.
3. Make a throwaway test board with the example persona (`skills/tailor-cvs/examples/master_cv.example.yaml`, "Alex Example").
   Never test with a real CV.
4. Run `find-jobs` or `tailor-cvs` by hand against that test board.
5. Delete the test board and any test scheduled tasks afterwards.

Your real board and scheduled tasks keep running the plugin you installed from this repo.

## Making a release

- Every pull request that changes anything under `plugins/` bumps `version` in
  `plugins/job-swipe/.claude-plugin/plugin.json` and adds a `plugins/job-swipe/CHANGELOG.md` entry with the same
  version. CI checks this. The "Board spec version" in `board-spec.md` (both places) and `BOARD_VERSION` in the
  reference board always equal that version, so bump them too, even when the board didn't change.
- A board design change means: change `board-spec.md`, make the reference board match it, and run
  `capture_spec_screens.py`. Existing boards only change when their owner accepts the rebuild that
  `/job-swipe-configure` offers, so describe board changes in the changelog in words people understand: Claude
  reads that entry to them.
- Before a release that touches the board spec or `cv-build.md`, build from them by hand: run
  `/job-swipe-configure` on a throwaway test board (example persona) and compare its screenshots with
  `board-screens/` side by side, light and dark; and make one tailored CV for the example job spec. Do the board
  build two or three times, since builds vary.

### Rolling back

There is no release branch. To undo a bad change: revert the commit in a new pull request, bump the patch version,
merge. Installs pick it up at their next update.

## Maintainer settings (one time, done by the owner)

- Protect `main`: require a pull request, require the `CI` checks to pass, block force-pushes and deletion. Don't
  turn on "Require review from Code Owners": the owner can't approve their own pull requests.
- Turn on private vulnerability reporting (Settings → Code security).
- Set the repository description and topics.

`.github/CODEOWNERS` asks the owner to review outside pull requests; it is a routing aid, not a second reviewer.

## Code of conduct

Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).
