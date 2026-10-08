# Job Swipe

Your own job feed, run by Claude.

- Twice a week (or as often as you like), Claude looks for jobs that match what you want and puts them on your **Job Swipe board**.
- You swipe on your phone: **right** = interested, **left** = not for me, **✓** = already applied. Add a short "why" to a swipe, and the next search uses it.
- Every job you swipe right on gets a **one-page CV made for that job**. It's built only from facts in your real CV and is easy for application systems to read. It's ready by the evening, under ♥.

You don't need to code. You need a paid **Claude plan (Pro or higher)** and the **Claude desktop app** for the first setup. After that, it all runs in the cloud, even when your laptop is closed, and you can swipe from the Claude phone app.

---

## Set it up (about 10 minutes)

**1. Add Job Swipe to Claude** (one time)

In the Claude desktop app, open **Customize** in the left sidebar, go to **Plugins**, click **Add**, choose **Add marketplace**, then **Add from a repository**, and enter:

```
cocchialorenzo9/job-swipe
```

Then install the **job-swipe** plugin from that list.

**2. Configure it**

Start a new task and type:

```
/job-swipe:configure
```

First, Claude asks for **your current CV** (PDF or Word). Add anything else that helps, like a LinkedIn PDF, a portfolio, or a job you'd love. Then it interviews you in short rounds about:

- **your experience in detail**: the achievements you're proudest of and the numbers behind them, your projects, your education, and the skills you'd happily be asked about,
- **the jobs you want**: roles, level, cities, languages, companies, deal-breakers,
- **the rhythm**: how often to search and when your CVs should be ready,
- **how your CV should look**: font, colour, length, section order. You see a real sample before anything is final.

Each question comes with Claude's suggestion, so "yes" is often enough. Nothing is built until you confirm the summary. Then Claude creates your private **Job Swipe board**, schedules everything, and, if you want, finds your first jobs right away.

**3. One switch to flip**

Open **Scheduled tasks** in Claude. Open each "Job Swipe" task and turn on **Automatically approve**. Otherwise the task waits for you to click "allow" instead of running on its own.

**Can't add plugins?** Type this in a new Claude task instead. It does the same thing:

```
Configure Job Swipe for me. Run: git clone --depth 1 https://github.com/cocchialorenzo9/job-swipe /tmp/job-swipe
then follow /tmp/job-swipe/plugins/job-swipe/skills/configure/SKILL.md
```

---

## Using it

- **Find your board:** it's in your Claude artifacts as "Job Swipe". Pin it so it's easy to find on your phone.
- **Change what you're looking for:** tap **⚙** on the board and edit your search brief. The next search uses it.
- **Change anything else** (how often, a new job on your CV, the CV look, pause): run `/job-swipe:configure` again. Claude sees your existing board and only asks about what you want to change.
- **Your data:** your board is private to your Claude account. Nobody else (including whoever shared this with you) can see your jobs, swipes or CV. CVs on the board are deleted after 7 days.
- **Usage:** each search uses a fair amount of your Claude usage. Twice a week is a good balance. The CV task stops right away on days with nothing new.

Claude never applies to jobs or contacts anyone for you. You always click **Apply** yourself.

---

## What's inside (for the curious)

| Part | What it does |
|---|---|
| `plugins/job-swipe/skills/configure` | The interview (in the style of [grilling](https://github.com/mattpocock/skills)), creating your board, scheduling, and later changes |
| `plugins/job-swipe/skills/find-jobs` | The search: reads your brief and swipes, searches, checks each job is live on the company site, adds cards |
| `plugins/job-swipe/skills/tailor-cvs` | Builds a one-page CV for each liked job (LaTeX, single column, readable by application systems) |
| `plugins/job-swipe/board/job-swipe.html` | The swipe board page |

Your scheduled tasks only point to these instructions; they don't copy them. When this repo gets better, the improvements reach you through plugin updates. You never redo the setup.

Ideas or problems? Tell Lorenzo.
