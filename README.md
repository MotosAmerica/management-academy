# Motos America Management Academy — Web Training Site

A mobile-friendly web version of the Management Academy manual: read all 23
modules, take instantly-scored quizzes, and unlock two full Part exams.
Each module review requires a perfect score to pass — a wrong answer sends
the trainee back to re-read the module rather than showing which answers
were right or wrong, so people have to actually revisit the material rather
than guess their way through. General Managers get a report showing who's
registered, who's passed each module, how many tries it took them, and each
Part exam score.

This manual serves **five roles in one site** — Sales Manager, Service
Manager, Parts Manager, F&I Manager, and General Manager — all reading the
same 23 modules. Part I (Modules 1–14) covers the frontline reality of
running a department: mindset, culture, people, and operating fundamentals,
including a cross-training pass through every other department. Part II
(Modules 15–23) covers advanced leadership, the General Manager relationship,
goal-setting, team-building, and the Apex Manager capstone. Every trainee
sees the full manual regardless of which role they log in as. Role only
affects the login dropdown and the manager report — it doesn't hide or
filter any content.

## What's in this repo

| File | Purpose |
|---|---|
| `index.html` | Page shell — loads everything else |
| `styles.css` | All visual design (shared Motos America Academy design system) |
| `content-data.js` | All 23 modules + every quiz question, generated from the locked manual |
| `app.js` | All app logic — login, navigation, quiz scoring, Supabase calls |
| `supabase-config.js` | Already filled in — points at the shared MAU Supabase project |
| `schema.sql` | Reference only, **plus one required one-time migration** — see below |

## One-time setup (do this before sharing the link with your team)

### Database — one migration required first

This site shares the **same Supabase project as every other MAU academy**
(Sales, Service Advisor, Parts & Accessories, F&I) rather than having one of
its own. The tables already exist, and `supabase-config.js` is already
pointed at it — there's no new project to create.

**However**, this site's role values need to match a set of five new
short names — `sales_manager`, `service_manager`, `parts_manager`,
`fi_manager`, and `gm` — since Management Academy's trainees are department
managers and General Managers, not the frontline roles other academies
already established. Before changing anything, confirm what's actually in
use:

```sql
select role, count(*) from trainees group by role order by role;
```

Then make sure the constraint permits every value you see there, plus the
five new manager role values if they aren't already present. Run this once
in the Supabase SQL Editor for the shared project (also included at the top
of `schema.sql`):

```sql
alter table trainees drop constraint if exists trainees_role_check;
alter table trainees add constraint trainees_role_check
  check (role in (
    'finance', 'sales', 'service_advisor', 'parts_associate',
    'sales_manager', 'service_manager', 'parts_manager', 'fi_manager', 'gm',
    'manager', 'admin'
  ));
```

This widens the constraint rather than replacing it — adjust the list to
include anything the `select` above turned up that isn't already here. The
MA Corporate constraint also needs widening in the same way, since prior
academies use `manager` for their MA Corporate rows while this academy uses
`gm` for the same purpose — both need to stay valid at once:

```sql
alter table trainees drop constraint if exists corporate_is_manager_only;
alter table trainees add constraint corporate_is_manager_only
  check (store <> 'MA Corporate' or role in ('manager', 'admin', 'gm'));
```

If another academy adds yet another role value later, that migration should
extend this same list rather than narrow it, since the constraint is
shared across every academy's rows in this one table.

Data stays cleanly separated: every row this site writes is tagged
`academy: 'management_academy'`, so it never mixes with Sales, Service,
Parts, or F&I data even though they all live in the same database.

If you ever need the connection details again, they live in the **Sales
Academy** Supabase project (`kairsmnztbvcxacdsizi`), not a project of this
site's own — Project Settings → API in that project.

Roles for this academy are **Sales Manager** (`sales_manager`), **Service
Manager** (`service_manager`), **Parts Manager** (`parts_manager`), **F&I
Manager** (`fi_manager`), and **General Manager** (`gm`) — five new role
values this academy introduces (an `admin` role also exists in the database
for anyone who needs full access without being tied to a specific store's
GM view — that role isn't in the login dropdown; create it directly in
Supabase's Table Editor if needed).

### 1. Turn on GitHub Pages
- In this repo on GitHub: **Settings → Pages**
- Under "Source," choose **Deploy from a branch**
- Branch: `main`, folder: `/ (root)`
- Save. GitHub will give you a URL like `https://motosamerica.github.io/management-academy/` within a minute or two

### 2. Give yourself General Manager access
- Log into the site once using your name, your store, and select **General
  Manager** as the role
- General Managers (and Admins) see an extra "Report" button in the top bar
  showing every trainee's progress

That's it — share the GitHub Pages URL with your team.

## Notes

- **No passwords.** Trainees log in with just their name and store. This is meant for internal use only — don't link this URL anywhere public.
- **Everyone gets the full manual.** Role doesn't gate content — a Sales Manager, a Service Manager, a Parts Manager, an F&I Manager, and a General Manager all see all 23 modules and both exams. Role is only used for the manager report and for identifying who's who.
- **Module reviews require 100%.** All 5 questions must be correct to pass. A wrong answer doesn't reveal which ones — the trainee is sent back to the module page to re-read, then can retry the review as many times as needed. The report shows how many attempts each person needed per module.
- **Part exams are not gated.** The two 20-question Part exams score and record the result, full answer review included, but don't block progress or require a retry.
- **Works offline-ish.** If wifi drops mid-quiz, the score still saves on the device and syncs to the shared database automatically once the connection is back.
- **Content changes:** if the manual content ever changes, `content-data.js` needs to be regenerated from the source (`manual_data.json`, via `build_content_data.py`) — it isn't meant to be hand-edited directly.
- **Logo:** `MA_logo_white_header.png` is the shared corporate logo used across all academy sites — already included in this repo.
