# Roadmap

Ideas that are agreed on but not built yet. Roughly in order; nothing here has a date.

## Launch polish

- A short demo GIF of swiping and opening a CV, at the top of the README.
- A sample board anyone can open without setting anything up.
- A small landing page.

## Board

- **Safe in-place board updates.** Today the board page is copied once, so fixes never reach existing boards. First
  check on a throwaway board that replacing the page keeps its data and stored CVs.
- **Card layout**: "Why it matched" right under the title; cards between 360 and 480 px tall instead of a fixed
  height with an empty gap.
- **All caught up** screen: add "Want more or different jobs? Edit what I'm looking for", opening ⚙.
- **Text labels under the round buttons**, so ✓ ("already applied") isn't mistaken for "yes".

## CVs

- Optional photo support, set up in one step instead of a long back-and-forth.
- A faster first CV build (today the first run installs LaTeX, which takes a few minutes).

## Project

- A release channel: plugin installs and the clone fallback follow tested releases instead of `main`.
- A linter for skill files (links between files resolve, required sections exist, no network commands).
