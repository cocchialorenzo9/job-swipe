# Scheduled-task prompts

Copy these exactly into `create_trigger` (`prompt`), replacing BOARD_URL with the person's board URL.
They stay short on purpose: the real instructions live in the Job Swipe kit on GitHub, so improvements reach
everyone without touching their tasks.

## Find jobs

```
Job Swipe: find new jobs for my board BOARD_URL.

Use the Skill tool to run `job-swipe:find-jobs` with the board URL as its argument and follow it.
If that skill is not available, run `git clone --depth 1 https://github.com/cocchialorenzo9/job-swipe /tmp/job-swipe`
and follow /tmp/job-swipe/plugins/job-swipe/skills/find-jobs/SKILL.md instead.

This runs on a schedule with nobody watching: never ask questions, make reasonable choices and finish.
```

## Tailored CVs

```
Job Swipe: make tailored CVs for the jobs I liked on my board BOARD_URL.

Use the Skill tool to run `job-swipe:tailor-cvs` with the board URL as its argument and follow it.
If that skill is not available, run `git clone --depth 1 https://github.com/cocchialorenzo9/job-swipe /tmp/job-swipe`
and follow /tmp/job-swipe/plugins/job-swipe/skills/tailor-cvs/SKILL.md instead.

This runs on a schedule with nobody watching: never ask questions, make reasonable choices and finish.
If there is nothing new to do, stop right away without sending a notification.
```
