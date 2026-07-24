create extension if not exists pgcrypto;
create schema if not exists private;

create table public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 120),
  status text not null default 'draft' check (status in ('draft','uploaded','analyzing','awaiting_review','queued','rendering','complete','failed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table public.assets (
  id uuid primary key default gen_random_uuid(), project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null check (kind in ('source_front','label_artwork','isolated_product','alpha_mask','render_front','render_three_quarter','render_ecommerce','model_glb','debug_manifest')),
  bucket text not null check (bucket in ('product-uploads','product-outputs')),
  object_path text not null check (object_path !~ '(^|/)\.\.(/|$)' and object_path !~ '^/'),
  mime_type text not null, byte_size bigint not null check (byte_size>0 and byte_size<=104857600),
  width integer check(width is null or width>0), height integer check(height is null or height>0), metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(), unique(bucket,object_path)
);
create table public.packaging_specs (
  id uuid primary key default gen_random_uuid(), project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade, version integer not null check(version>0),
  schema_version text not null check(schema_version='1.0.0'), spec jsonb not null, is_approved boolean not null default false,
  created_at timestamptz not null default now(), unique(project_id,version)
);
create table public.render_jobs (
  id uuid primary key default gen_random_uuid(), project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade, status text not null default 'queued' check(status in ('queued','rendering','complete','failed')),
  current_step text not null default 'validating specification', attempt_count integer not null default 0 check(attempt_count between 0 and 3),
  locked_at timestamptz, locked_by text, error_code text, error_message text, started_at timestamptz, completed_at timestamptz,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  check((status='failed') or (error_code is null and error_message is null))
);
create index projects_user_created_idx on public.projects(user_id,created_at desc);
create index assets_project_kind_idx on public.assets(project_id,kind);
create index packaging_specs_project_version_idx on public.packaging_specs(project_id,version desc);
create index render_jobs_queue_idx on public.render_jobs(status,created_at) where status='queued';
create index render_jobs_stale_idx on public.render_jobs(locked_at) where status='rendering';
create or replace function private.set_updated_at() returns trigger language plpgsql security invoker set search_path='' as $$begin new.updated_at=now();return new;end;$$;
create trigger projects_updated before update on public.projects for each row execute function private.set_updated_at();
create trigger render_jobs_updated before update on public.render_jobs for each row execute function private.set_updated_at();
alter table public.projects enable row level security;alter table public.assets enable row level security;alter table public.packaging_specs enable row level security;alter table public.render_jobs enable row level security;
create policy projects_select on public.projects for select to authenticated using((select auth.uid())=user_id);
create policy projects_insert on public.projects for insert to authenticated with check((select auth.uid())=user_id);
create policy projects_update on public.projects for update to authenticated using((select auth.uid())=user_id) with check((select auth.uid())=user_id);
create policy projects_delete on public.projects for delete to authenticated using((select auth.uid())=user_id);
create policy assets_select on public.assets for select to authenticated using((select auth.uid())=user_id);
create policy assets_insert on public.assets for insert to authenticated with check((select auth.uid())=user_id and exists(select 1 from public.projects p where p.id=project_id and p.user_id=(select auth.uid())));
create policy assets_update on public.assets for update to authenticated using((select auth.uid())=user_id) with check((select auth.uid())=user_id and exists(select 1 from public.projects p where p.id=project_id and p.user_id=(select auth.uid())));
create policy assets_delete on public.assets for delete to authenticated using((select auth.uid())=user_id);
create policy specs_select on public.packaging_specs for select to authenticated using((select auth.uid())=user_id);
create policy specs_insert on public.packaging_specs for insert to authenticated with check((select auth.uid())=user_id and exists(select 1 from public.projects p where p.id=project_id and p.user_id=(select auth.uid())));
create policy specs_update on public.packaging_specs for update to authenticated using((select auth.uid())=user_id) with check((select auth.uid())=user_id and exists(select 1 from public.projects p where p.id=project_id and p.user_id=(select auth.uid())));
create policy jobs_select on public.render_jobs for select to authenticated using((select auth.uid())=user_id);
create policy jobs_insert on public.render_jobs for insert to authenticated with check((select auth.uid())=user_id and exists(select 1 from public.packaging_specs s where s.project_id=project_id and s.user_id=(select auth.uid()) and s.is_approved));
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types) values
('product-uploads','product-uploads',false,15728640,array['image/png','image/jpeg','image/webp']),
('product-outputs','product-outputs',false,52428800,array['image/png','model/gltf-binary','application/json'])
on conflict(id) do update set public=false,file_size_limit=excluded.file_size_limit,allowed_mime_types=excluded.allowed_mime_types;
create policy storage_owner_read on storage.objects for select to authenticated using(bucket_id in('product-uploads','product-outputs') and (storage.foldername(name))[1]=(select auth.uid())::text);
create policy storage_owner_insert on storage.objects for insert to authenticated with check(bucket_id in('product-uploads','product-outputs') and (storage.foldername(name))[1]=(select auth.uid())::text);
create policy storage_owner_update on storage.objects for update to authenticated using(bucket_id in('product-uploads','product-outputs') and (storage.foldername(name))[1]=(select auth.uid())::text) with check(bucket_id in('product-uploads','product-outputs') and (storage.foldername(name))[1]=(select auth.uid())::text);
create policy storage_owner_delete on storage.objects for delete to authenticated using(bucket_id in('product-uploads','product-outputs') and (storage.foldername(name))[1]=(select auth.uid())::text);
create or replace function public.claim_render_job(p_job_id uuid,p_worker_id text) returns setof public.render_jobs language sql security invoker set search_path='' as $$
update public.render_jobs j set status='rendering',locked_at=now(),locked_by=p_worker_id,attempt_count=j.attempt_count+1,started_at=coalesce(j.started_at,now()),current_step='validating specification',error_code=null,error_message=null
where j.id=p_job_id and j.attempt_count<3 and (j.status='queued' or (j.status='rendering' and j.locked_at<now()-interval '15 minutes')) returning j.*;$$;
revoke all on function public.claim_render_job(uuid,text) from public,anon,authenticated;grant execute on function public.claim_render_job(uuid,text) to service_role;
grant select,insert,update,delete on public.projects to authenticated;grant select,insert,update,delete on public.assets to authenticated;grant select,insert,update on public.packaging_specs to authenticated;grant select,insert on public.render_jobs to authenticated;
