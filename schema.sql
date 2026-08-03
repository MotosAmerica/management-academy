-- Motos America Management Academy — Supabase schema (reference only)
-- This academy shares the same Supabase project/tables as every other MAU
-- academy. These tables already exist — this file documents what they look
-- like and what to run if a role value below isn't yet permitted.
--
-- ONE-TIME ACTION REQUIRED FOR THIS ACADEMY:
-- The live `trainees` table's role CHECK constraint needs to permit the
-- five role values this site actually writes: 'sales_manager',
-- 'service_manager', 'parts_manager', 'fi_manager', and 'gm' (General
-- Manager) — new role values, since Management Academy's trainees are
-- department managers and GMs, not the frontline roles other academies use.
-- 'admin' should already be permitted from prior academies. Run this once
-- in the Supabase SQL Editor for the shared project:
--
--   alter table trainees drop constraint if exists trainees_role_check;
--   alter table trainees add constraint trainees_role_check
--     check (role in (
--       'finance', 'sales', 'service_advisor', 'parts_associate',
--       'sales_manager', 'service_manager', 'parts_manager', 'fi_manager', 'gm',
--       'manager', 'admin'
--     ));
--
-- Before running any constraint change, confirm what's actually live:
--   select role, count(*) from trainees group by role order by role;
-- and fold any role value you see there into the list above, since this
-- constraint is shared across every academy's rows in this one table.
--
-- The MA Corporate constraint below also needs widening, since prior
-- academies use 'manager' for their MA Corporate rows while this academy
-- uses 'gm' for the same purpose. Both need to stay valid:
--
--   alter table trainees drop constraint if exists corporate_is_manager_only;
--   alter table trainees add constraint corporate_is_manager_only
--     check (store <> 'MA Corporate' or role in ('manager', 'admin', 'gm'));

-- Trainees (no password auth; just name + store selection)
create table if not exists trainees (
  id uuid primary key default gen_random_uuid(),
  full_name text not null,
  store text not null check (store in ('Cascade Moto Portland', 'Tampa Bay Motos', 'Triumph of Santa Monica', 'Triumph Columbia River', 'MA Corporate')),
  role text not null default 'sales_manager' check (role in (
    'finance', 'sales', 'service_advisor', 'parts_associate',
    'sales_manager', 'service_manager', 'parts_manager', 'fi_manager', 'gm',
    'manager', 'admin'
  )),
  -- MA Corporate is a manager-only "store" (used for corporate staff, not a
  -- physical dealership) — this constraint makes it impossible to insert a
  -- non-manager row for it, even via a direct API call bypassing the site.
  -- 'gm' is this academy's version of that top-level role; 'manager' covers
  -- the same case for academies that predate this one.
  constraint corporate_is_manager_only check (
    store <> 'MA Corporate' or role in ('manager', 'admin', 'gm')
  ),
  created_at timestamptz not null default now()
);

-- One row per quiz/exam attempt
create table if not exists quiz_attempts (
  id uuid primary key default gen_random_uuid(),
  trainee_id uuid not null references trainees(id) on delete cascade,
  quiz_key text not null,           -- e.g. 'module-1', 'part1-exam', 'part2-exam'
  quiz_label text not null,         -- human readable, e.g. 'Module 01 Review'
  total_questions int not null,
  correct_answers int not null,
  score_pct numeric not null,
  answers jsonb not null,           -- the raw answers given, for review
  attempt_number int not null default 1,  -- 1st try, 2nd try, etc. Module reviews
                                            -- require a perfect score to pass, so this
                                            -- shows how many tries it took someone.
  completed_at timestamptz not null default now()
);

-- Helpful index for the report dashboard
create index if not exists idx_attempts_trainee on quiz_attempts(trainee_id);
create index if not exists idx_attempts_quiz_key on quiz_attempts(quiz_key);

-- Row Level Security: allow anon key to insert/select (fine at this scale, this is an internal tool)
alter table trainees enable row level security;
alter table quiz_attempts enable row level security;

create policy "anyone can read trainees" on trainees for select using (true);
create policy "anyone can insert trainees" on trainees for insert with check (true);

create policy "anyone can read attempts" on quiz_attempts for select using (true);
create policy "anyone can insert attempts" on quiz_attempts for insert with check (true);
