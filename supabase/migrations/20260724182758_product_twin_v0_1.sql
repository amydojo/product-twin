-- Product Twin v0.1 schema
create extension if not exists pgcrypto;

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.assets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null check (kind in ('reference','label','render','model','manifest')),
  storage_path text not null,
  content_type text,
  byte_size bigint,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.product_specs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  version integer not null default 1,
  spec jsonb not null,
  created_at timestamptz not null default now(),
  unique (project_id, version)
);

create table if not exists public.render_jobs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'queued' check (status in ('queued','analyzing','modeling','rendering','uploading','succeeded','failed','cancelled')),
  input_spec jsonb not null,
  result_manifest jsonb,
  error_code text,
  error_message text,
  created_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz
);

create index if not exists projects_user_id_idx on public.projects(user_id);
create index if not exists assets_project_id_idx on public.assets(project_id);
create index if not exists assets_user_id_idx on public.assets(user_id);
create index if not exists product_specs_project_id_idx on public.product_specs(project_id);
create index if not exists product_specs_user_id_idx on public.product_specs(user_id);
create index if not exists render_jobs_project_id_idx on public.render_jobs(project_id);
create index if not exists render_jobs_user_id_idx on public.render_jobs(user_id);
create index if not exists render_jobs_status_idx on public.render_jobs(status);

alter table public.projects enable row level security;
alter table public.assets enable row level security;
alter table public.product_specs enable row level security;
alter table public.render_jobs enable row level security;

create policy "projects_select_own" on public.projects for select to authenticated using ((select auth.uid()) = user_id);
create policy "projects_insert_own" on public.projects for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "projects_update_own" on public.projects for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "projects_delete_own" on public.projects for delete to authenticated using ((select auth.uid()) = user_id);

create policy "assets_select_own" on public.assets for select to authenticated using ((select auth.uid()) = user_id);
create policy "assets_insert_own" on public.assets for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "assets_update_own" on public.assets for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "assets_delete_own" on public.assets for delete to authenticated using ((select auth.uid()) = user_id);

create policy "product_specs_select_own" on public.product_specs for select to authenticated using ((select auth.uid()) = user_id);
create policy "product_specs_insert_own" on public.product_specs for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "product_specs_update_own" on public.product_specs for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "product_specs_delete_own" on public.product_specs for delete to authenticated using ((select auth.uid()) = user_id);

create policy "render_jobs_select_own" on public.render_jobs for select to authenticated using ((select auth.uid()) = user_id);
create policy "render_jobs_insert_own" on public.render_jobs for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "render_jobs_update_own" on public.render_jobs for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "render_jobs_delete_own" on public.render_jobs for delete to authenticated using ((select auth.uid()) = user_id);

grant usage on schema public to authenticated;
grant select, insert, update, delete on public.projects, public.assets, public.product_specs, public.render_jobs to authenticated;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'product-twin-assets',
  'product-twin-assets',
  false,
  52428800,
  array['image/png','image/jpeg','image/webp','image/svg+xml','model/gltf-binary','application/json']
)
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create policy "storage_select_own" on storage.objects for select to authenticated using (
  bucket_id = 'product-twin-assets' and (storage.foldername(name))[1] = (select auth.uid())::text
);
create policy "storage_insert_own" on storage.objects for insert to authenticated with check (
  bucket_id = 'product-twin-assets' and (storage.foldername(name))[1] = (select auth.uid())::text
);
create policy "storage_update_own" on storage.objects for update to authenticated using (
  bucket_id = 'product-twin-assets' and (storage.foldername(name))[1] = (select auth.uid())::text
) with check (
  bucket_id = 'product-twin-assets' and (storage.foldername(name))[1] = (select auth.uid())::text
);
create policy "storage_delete_own" on storage.objects for delete to authenticated using (
  bucket_id = 'product-twin-assets' and (storage.foldername(name))[1] = (select auth.uid())::text
);