-- REVIEWED SCHEMA PROPOSAL. Do not apply to an unrelated Supabase project.
-- Generate an official migration with `supabase migration new website_inquiries`
-- in the dedicated MMEd project, then copy these statements into that file.
-- Confidential B2B contact information only. Never store PHI.
create table if not exists public.website_inquiries (
  id uuid primary key default gen_random_uuid(),
  submitted_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  full_name text not null check (char_length(full_name) between 2 and 120),
  work_email text not null check (char_length(work_email) between 6 and 254),
  organization text not null check (char_length(organization) between 2 and 160),
  job_title text not null check (char_length(job_title) between 2 and 100),
  country text not null check (char_length(country) between 2 and 90),
  time_zone text not null check (char_length(time_zone) between 2 and 80),
  facility_type text not null check (facility_type in
    ('private_clinic','medical_center','hospital','care_network','healthcare_operator','other')),
  locations text not null check (char_length(locations) between 1 and 50),
  interests text[] not null default '{}'::text[],
  timeline text not null check (timeline in
    ('exploring','within_3_months','three_to_twelve_months','later')),
  message text not null default '' check (char_length(message) <= 1000),
  inquiry_source text not null default 'public_website',
  ip_hash text not null check (char_length(ip_hash) = 64),
  status text not null default 'new' check (status in
    ('new','contacted','qualified','demo_invited','won','closed')),
  notification_status text not null default 'pending'
    check (notification_status in ('pending','sent','failed')),
  notification_id text,
  privacy_notice_accepted boolean not null check (privacy_notice_accepted = true),
  no_phi_confirmed boolean not null check (no_phi_confirmed = true)
);
create index if not exists website_inquiries_submitted_at_idx on public.website_inquiries (submitted_at desc);
create index if not exists website_inquiries_ip_limit_idx on public.website_inquiries (ip_hash, submitted_at desc);
create index if not exists website_inquiries_email_limit_idx on public.website_inquiries (work_email, submitted_at desc);
alter table public.website_inquiries enable row level security;
-- Public forms write through a server-only Edge Function, NEVER via anon/authenticated Data API.
revoke all privileges on table public.website_inquiries from public, anon, authenticated;
grant select, insert, update on public.website_inquiries to service_role;
-- No public policies. service_role bypasses RLS; this key must stay server-side.
-- Set a formal 90-day retention/erasure workflow before enabling production intake.
