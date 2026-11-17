# Scheduled-task prompts

Copy these exactly into `create_trigger` (`prompt`), replacing BOARD_URL with the person's board URL.
They stay short on purpose: the real instructions live in the installed Job Swipe plugin, so improvements reach
everyone through plugin updates without touching their tasks. A task never downloads instructions from anywhere
else: if the plugin isn't there, it says so and stops.

## Find jobs

```
Job Swipe: find new jobs for my board BOARD_URL.

Use the Skill tool to run `job-swipe:find-jobs` with the board URL as its argument and follow it.
If that skill is not available, change nothing, send one notification "Job Swipe isn't installed where this
task runs: add the job-swipe plugin in Claude, then ask Claude to 'configure Job Swipe'" and stop.

This runs on a schedule with nobody watching: never ask questions, make reasonable choices and finish.
```

## Tailored CVs

```
Job Swipe: make tailored CVs for the jobs I liked on my board BOARD_URL.

Use the Skill tool to run `job-swipe:tailor-cvs` with the board URL as its argument and follow it.
If that skill is not available, change nothing, send one notification "Job Swipe isn't installed where this
task runs: add the job-swipe plugin in Claude, then ask Claude to 'configure Job Swipe'" and stop.

This runs on a schedule with nobody watching: never ask questions, make reasonable choices and finish.
If there is nothing new to do, stop right away without sending a notification.
```
