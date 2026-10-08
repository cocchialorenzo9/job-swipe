# How to run the interview ("grilling")

Adapted for Job Swipe from Matt Pocock's `grilling` skill (MIT): https://github.com/mattpocock/skills

Interview the person until you both have the same picture of what will be built: their CV facts, the jobs to
look for, the rhythm, and how the CV should look. Treat it as a **design tree** (`design-tree.md`): every decision
opens the decisions that hang off it.

## Rounds and the frontier

Work in **rounds**. The **frontier** is every open question whose prerequisites are already settled — what you can
ask *now* without guessing at answers you haven't heard. Ask the whole frontier in one round, then wait.
A question that depends on another question still open in this round belongs to a *later* round.

These people are not developers, and many write in a second language, so:
- Keep a round to **at most 5 questions**. If the frontier is bigger, ask the 5 that unblock the most.
- Short, plain sentences. No jargon (no "ATS", "YAML", "cron": say "application systems", "your CV details",
  "how often").
- If the person says "one at a time", switch to one question per message for the rest of the session.

## Question format

```
❓ **Q1 · <short title>**: <the question; options as a short list if it's a choice>

➡️ <your recommended answer, and in a few words why>

---

❓ **Q2 · <short title>**: ...

➡️ ...
```

- Word each question so that **"yes" accepts your recommendation** ("Shall we keep it to one page?" — not "One or
  two pages?").
- Tell them once, at the start: "You can answer by number, like '1 yes, 2 Berlin only, 3 skip'."
- Every recommendation must be specific to them (their CV, their field, their country), not generic advice.

## Facts vs decisions

- **Facts are your job.** Never ask what their CV, LinkedIn export, portfolio or the web already answers. Read it
  first. Where you extracted something, show it and ask them to confirm ("I read these 4 roles — yes if right").
- **Facts only they know** (numbers behind an achievement, team size, what they personally did, which skills they
  could defend in an interview) are questions — ask them, with an example of the kind of answer you need:
  "How much faster was it after your change? e.g. 'from 3 days to 4 hours'."
- **Decisions are theirs.** Recommend, then wait. Never answer your own question.
- When a fact needs a lookup (e.g. typical job titles for their field in their city), look it up yourself; only
  the questions that depend on that lookup wait for it.

## Answers move the tree

Each round of answers settles decisions and opens new ones. Recompute the frontier from scratch every round.
If a later answer changes an earlier decision, reopen that branch in the next round and say so.

## Done

The interview is done when the frontier is empty: every branch visited, nothing silently assumed. Then write the
**shared-understanding summary** (see SKILL.md) and **do not build anything until they confirm it**.
