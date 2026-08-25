-- ScamShield AI — Supabase schema
-- Run this in the Supabase SQL editor for your project.
-- Implements Phase 5 (auth + history + dashboard) storage per the spec.
-- Row Level Security ensures users can only ever see their own analyses.

-- Profiles table (extends Supabase auth.users)
create table if not exists public.profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "Users can view their own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can update their own profile"
  on public.profiles for update
  using (auth.uid() = id);

-- Auto-create a profile row when a new user signs up
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Analyses table: stores every submitted analysis + full structured result
create table if not exists public.analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users on delete cascade not null,
  input_type text not null check (input_type in ('text', 'url', 'image', 'combined')),
  input_summary text not null,
  overall_risk_score numeric not null,
  risk_level text not null check (risk_level in ('Low', 'Medium', 'High', 'Critical')),
  scam_category text,
  confidence numeric,
  evidence jsonb,
  signals jsonb,
  text_analysis jsonb,
  url_analysis jsonb,
  ocr jsonb,
  ai_investigation jsonb,
  image_storage_path text,
  created_at timestamptz default now()
);

create index if not exists analyses_user_id_idx on public.analyses (user_id);
create index if not exists analyses_created_at_idx on public.analyses (created_at desc);

alter table public.analyses enable row level security;

create policy "Users can view their own analyses"
  on public.analyses for select
  using (auth.uid() = user_id);

create policy "Users can insert their own analyses"
  on public.analyses for insert
  with check (auth.uid() = user_id);

create policy "Users can delete their own analyses"
  on public.analyses for delete
  using (auth.uid() = user_id);

-- Storage bucket for uploaded screenshots (private, per-user access via RLS-style policy)
insert into storage.buckets (id, name, public)
values ('scam-screenshots', 'scam-screenshots', false)
on conflict (id) do nothing;

create policy "Users can upload their own screenshots"
  on storage.objects for insert
  with check (bucket_id = 'scam-screenshots' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "Users can view their own screenshots"
  on storage.objects for select
  using (bucket_id = 'scam-screenshots' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "Users can delete their own screenshots"
  on storage.objects for delete
  using (bucket_id = 'scam-screenshots' and (storage.foldername(name))[1] = auth.uid()::text);
