# Security

Job Swipe runs unattended in people's Claude accounts, reads web pages written by strangers, and holds their CV.
Please report anything that could hurt someone using it.

## How to report

Use GitHub's private reporting: on this repository, open **Security → Report a vulnerability**. Only the
maintainer sees the report.

If that button isn't there, open an issue titled **"Security contact request"** with no details. The maintainer
will reach out and agree on a private channel with you.

Please don't publish the details until a fix is out. You'll get a first answer within a week.

## In scope

- The skills (`plugins/job-swipe/skills/`) and their shared rules (`plugins/job-swipe/references/`).
- The board page (`plugins/job-swipe/board/job-swipe.html`).
- The CV builder (`plugins/job-swipe/skills/tailor-cvs/cv/`).

Examples: a job page that makes the agent leak CV or contact data, run commands or change the board; script
injection (XSS) on the board; anything that deletes a board or someone's stored CVs; a posting text that breaks CV
builds for everyone.

Out of scope: Claude itself, the Claude apps and the artifact sandbox (report those to Anthropic), and job sites.

## What the rules can and can't do

The untrusted-content rules in `plugins/job-swipe/references/board-data.md` tell Claude to treat web text as data,
to skip pages that try to make it act, and never to send personal data anywhere. They are instructions to a model,
not a sandbox: they lower the risk of a page tricking the agent, they don't remove it. Reports that show a way
around them are welcome.
