-- Reconcile the empty live prototype schema with the repository contract.
-- Abort rather than discard data if this migration encounters a populated prototype.
do $$
declare
  schema_is_current boolean;
  prototype_rows bigint;
  product_spec_rows bigint := 0;
  prototype_objects bigint;
begin
  select
    to_regclass('public.packaging_specs') is not null
    and exists (
      select 1 from information_schema.columns
      where table_schema = 'public' and table_name = 'projects' and column_name = 'status'
    )
    and exists (
      select 1 from information_schema.columns
      where table_schema = 'public' and table_name = 'assets' and column_name = 'object_path'
    )
    and exists (
      select 1 from information_schema.columns
      where table_schema = 'public' and table_name = 'render_jobs' and column_name = 'attempt_count'
    )
  into schema_is_current;

  if not schema_is_current then
    if to_regclass('public.product_specs') is not null then
      execute 'select count(*) from public.product_specs' into product_spec_rows;
    end if;

    select
      coalesce((select count(*) from public.projects), 0)
      + coalesce((select count(*) from public.assets), 0)
      + coalesce((select count(*) from public.render_jobs), 0)
      + product_spec_rows
    into prototype_rows;

    select count(*)
    into prototype_objects
    from storage.objects
    where bucket_id = 'product-twin-assets';

    if prototype_rows <> 0 or prototype_objects <> 0 then
      raise exception
        'Product Twin prototype schema contains % rows and % objects; guarded reconciliation stopped',
        prototype_rows,
        prototype_objects;
    end if;

    drop table if exists public.render_jobs cascade;
    drop table if exists public.product_specs cascade;
    drop table if exists public.packaging_specs cascade;
    drop table if exists public.assets cascade;
    drop table if exists public.projects cascade;
  end if;
end
$$;

drop policy if exists storage_select_own on storage.objects;
drop policy if exists storage_insert_own on storage.objects;
drop policy if exists storage_update_own on storage.objects;
drop policy if exists storage_delete_own on storage.objects;
drop policy if exists storage_owner_read on storage.objects;
drop policy if exists storage_owner_insert on storage.objects;
drop policy if exists storage_owner_update on storage.objects;
drop policy if exists storage_owner_delete on storage.objects;

-- Supabase Storage protects direct deletes unless the same transaction opts in.
-- The guard above has already proved both the prototype tables and bucket empty.
select set_config('storage.allow_delete_query', 'true', true);
delete from storage.buckets
where id = 'product-twin-assets'
  and not exists (
    select 1 from storage.objects where bucket_id = 'product-twin-assets'
  );

create schema if not exists private;

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 120),
  status text not null default 'draft' check (
    status in (
      'draft',
      'uploaded',
      'analyzing',
      'awaiting_review',
      'queued',
      'rendering',
      'complete',
      'failed'
    )
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.assets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null check (
    kind in (
      'source_front',
      'label_artwork',
      'isolated_product',
      'alpha_mask',
      'render_front',
      'render_three_quarter',
      'render_ecommerce',
      'model_glb',
      'debug_manifest'
    )
  ),
  bucket text not null check (bucket in ('product-uploads', 'product-outputs')),
  object_path text not null check (
    object_path !~ '(^|/)\.\.(/|$)'
    and object_path !~ '^/'
  ),
  mime_type text not null,
  byte_size bigint not null check (byte_size > 0 and byte_size <= 104857600),
  width integer check (width is null or width > 0),
  height integer check (height is null or height > 0),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (bucket, object_path)
);

create table if not exists public.packaging_specs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  version integer not null check (version > 0),
  schema_version text not null check (schema_version = '1.0.0'),
  spec jsonb not null,
  is_approved boolean not null default false,
  created_at timestamptz not null default now(),
  unique (project_id, version)
);

create table if not exists public.render_jobs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'queued' check (
    status in ('queued', 'rendering', 'complete', 'failed')
  ),
  current_step text not null default 'validating specification',
  attempt_count integer not null default 0 check (attempt_count between 0 and 3),
  locked_at timestamptz,
  locked_by text,
  error_code text,
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check ((status = 'failed') or (error_code is null and error_message is null))
);

create index if not exists projects_user_created_idx
  on public.projects(user_id, created_at desc);
create index if not exists assets_project_kind_idx
  on public.assets(project_id, kind);
create index if not exists packaging_specs_project_version_idx
  on public.packaging_specs(project_id, version desc);
create index if not exists render_jobs_queue_idx
  on public.render_jobs(status, created_at)
  where status = 'queued';
create index if not exists render_jobs_stale_idx
  on public.render_jobs(locked_at)
  where status = 'rendering';

create or replace function private.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;
revoke all on function private.set_updated_at() from public, anon, authenticated;

drop trigger if exists projects_updated on public.projects;
create trigger projects_updated
before update on public.projects
for each row execute function private.set_updated_at();

drop trigger if exists render_jobs_updated on public.render_jobs;
create trigger render_jobs_updated
before update on public.render_jobs
for each row execute function private.set_updated_at();

alter table public.projects enable row level security;
alter table public.assets enable row level security;
alter table public.packaging_specs enable row level security;
alter table public.render_jobs enable row level security;

drop policy if exists projects_select on public.projects;
drop policy if exists projects_insert on public.projects;
drop policy if exists projects_update on public.projects;
drop policy if exists projects_delete on public.projects;
create policy projects_select on public.projects
  for select to authenticated using ((select auth.uid()) = user_id);
create policy projects_insert on public.projects
  for insert to authenticated with check ((select auth.uid()) = user_id);
create policy projects_update on public.projects
  for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
create policy projects_delete on public.projects
  for delete to authenticated using ((select auth.uid()) = user_id);

drop policy if exists assets_select on public.assets;
drop policy if exists assets_insert on public.assets;
drop policy if exists assets_update on public.assets;
drop policy if exists assets_delete on public.assets;
create policy assets_select on public.assets
  for select to authenticated using ((select auth.uid()) = user_id);
create policy assets_insert on public.assets
  for insert to authenticated
  with check (
    (select auth.uid()) = user_id
    and exists (
      select 1
      from public.projects project
      where project.id = project_id
        and project.user_id = (select auth.uid())
    )
  );
create policy assets_update on public.assets
  for update to authenticated
  using ((select auth.uid()) = user_id)
  with check (
    (select auth.uid()) = user_id
    and exists (
      select 1
      from public.projects project
      where project.id = project_id
        and project.user_id = (select auth.uid())
    )
  );
create policy assets_delete on public.assets
  for delete to authenticated using ((select auth.uid()) = user_id);

drop policy if exists specs_select on public.packaging_specs;
drop policy if exists specs_insert on public.packaging_specs;
drop policy if exists specs_update on public.packaging_specs;
create policy specs_select on public.packaging_specs
  for select to authenticated using ((select auth.uid()) = user_id);
create policy specs_insert on public.packaging_specs
  for insert to authenticated
  with check (
    (select auth.uid()) = user_id
    and exists (
      select 1
      from public.projects project
      where project.id = project_id
        and project.user_id = (select auth.uid())
    )
  );
create policy specs_update on public.packaging_specs
  for update to authenticated
  using ((select auth.uid()) = user_id)
  with check (
    (select auth.uid()) = user_id
    and exists (
      select 1
      from public.projects project
      where project.id = project_id
        and project.user_id = (select auth.uid())
    )
  );

drop policy if exists jobs_select on public.render_jobs;
drop policy if exists jobs_insert on public.render_jobs;
drop policy if exists jobs_fail on public.render_jobs;
create policy jobs_select on public.render_jobs
  for select to authenticated using ((select auth.uid()) = user_id);
create policy jobs_insert on public.render_jobs
  for insert to authenticated
  with check (
    (select auth.uid()) = user_id
    and exists (
      select 1
      from public.packaging_specs spec
      where spec.project_id = project_id
        and spec.user_id = (select auth.uid())
        and spec.is_approved
    )
  );
create policy jobs_fail on public.render_jobs
  for update to authenticated
  using (
    (select auth.uid()) = user_id
    and status = 'queued'
    and locked_at is null
    and locked_by is null
  )
  with check (
    (select auth.uid()) = user_id
    and status = 'failed'
    and current_step = 'failed'
    and locked_at is null
    and locked_by is null
    and error_code in ('worker_unavailable', 'worker_start_failed')
    and error_message is not null
    and completed_at is not null
  );

insert into storage.buckets(id, name, public, file_size_limit, allowed_mime_types)
values
  (
    'product-uploads',
    'product-uploads',
    false,
    15728640,
    array['image/png', 'image/jpeg', 'image/webp']
  ),
  (
    'product-outputs',
    'product-outputs',
    false,
    52428800,
    array['image/png', 'model/gltf-binary', 'application/json']
  )
on conflict(id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create policy storage_owner_read on storage.objects
  for select to authenticated
  using (
    bucket_id in ('product-uploads', 'product-outputs')
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );
create policy storage_owner_insert on storage.objects
  for insert to authenticated
  with check (
    bucket_id in ('product-uploads', 'product-outputs')
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );
create policy storage_owner_update on storage.objects
  for update to authenticated
  using (
    bucket_id in ('product-uploads', 'product-outputs')
    and (storage.foldername(name))[1] = (select auth.uid())::text
  )
  with check (
    bucket_id in ('product-uploads', 'product-outputs')
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );
create policy storage_owner_delete on storage.objects
  for delete to authenticated
  using (
    bucket_id in ('product-uploads', 'product-outputs')
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create or replace function public.claim_render_job(p_job_id uuid, p_worker_id text)
returns setof public.render_jobs
language sql
security invoker
set search_path = ''
as $$
  update public.render_jobs job
  set
    status = 'rendering',
    locked_at = now(),
    locked_by = p_worker_id,
    attempt_count = job.attempt_count + 1,
    started_at = coalesce(job.started_at, now()),
    current_step = 'validating specification',
    error_code = null,
    error_message = null
  where job.id = p_job_id
    and job.attempt_count < 3
    and (
      job.status = 'queued'
      or (
        job.status = 'rendering'
        and job.locked_at < now() - interval '15 minutes'
      )
    )
  returning job.*;
$$;

revoke all on function public.claim_render_job(uuid, text) from public, anon, authenticated;
grant execute on function public.claim_render_job(uuid, text) to service_role;

grant usage on schema public to authenticated, service_role;
revoke all on public.projects, public.assets, public.packaging_specs, public.render_jobs
  from public, anon, authenticated, service_role;
grant select, insert, update, delete on public.projects to authenticated;
grant select, insert on public.assets to authenticated;
grant select, insert, update on public.packaging_specs to authenticated;
grant select, insert on public.render_jobs to authenticated;
grant update(status, current_step, error_code, error_message, completed_at)
  on public.render_jobs
  to authenticated;
grant select, insert, update, delete
  on public.projects, public.assets, public.packaging_specs, public.render_jobs
  to service_role;
