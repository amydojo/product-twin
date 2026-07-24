create extension if not exists pgtap with schema extensions;
set search_path = public, extensions;
begin;
select plan(27);

insert into auth.users (id, aud, role, email, created_at, updated_at)
values
  ('11111111-1111-1111-1111-111111111111', 'authenticated', 'authenticated', 'a@example.test', now(), now()),
  ('22222222-2222-2222-2222-222222222222', 'authenticated', 'authenticated', 'b@example.test', now(), now());

set local role authenticated;
select set_config('request.jwt.claim.sub', '11111111-1111-1111-1111-111111111111', true);

insert into public.projects (id, user_id, name)
values ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'Owner project');

select is(
  (select count(*)::int from public.projects),
  1,
  'owner can read own project'
);
select throws_ok(
  $$update public.projects
    set user_id = '22222222-2222-2222-2222-222222222222'
    where id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'$$,
  '42501',
  null,
  'owner cannot reassign project ownership'
);

insert into public.assets (
  id,
  project_id,
  user_id,
  kind,
  bucket,
  object_path,
  mime_type,
  byte_size
)
values (
  'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '11111111-1111-1111-1111-111111111111',
  'source_front',
  'product-uploads',
  '11111111-1111-1111-1111-111111111111/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/source.png',
  'image/png',
  12
);
select is(
  (select count(*)::int from public.assets),
  1,
  'owner can create an asset for own project'
);

insert into public.packaging_specs (
  id,
  project_id,
  user_id,
  version,
  schema_version,
  spec,
  is_approved
)
values (
  'cccccccc-cccc-cccc-cccc-cccccccccccc',
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '11111111-1111-1111-1111-111111111111',
  1,
  '1.0.0',
  '{}'::jsonb,
  true
);
select is(
  (select count(*)::int from public.packaging_specs where is_approved),
  1,
  'owner can approve a specification for own project'
);

insert into public.render_jobs (
  id,
  project_id,
  user_id
)
values (
  'dddddddd-dddd-dddd-dddd-dddddddddddd',
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  '11111111-1111-1111-1111-111111111111'
);
select is(
  (select count(*)::int from public.render_jobs),
  1,
  'owner can queue a job only after approval'
);

insert into storage.objects (bucket_id, name, owner_id, metadata)
values (
  'product-uploads',
  '11111111-1111-1111-1111-111111111111/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/source.png',
  '11111111-1111-1111-1111-111111111111',
  '{}'::jsonb
);
select is(
  (
    select count(*)::int
    from storage.objects
    where bucket_id = 'product-uploads'
  ),
  1,
  'owner can create an object in own storage prefix'
);
select is(
  (
    select count(*)::int
    from storage.objects
    where bucket_id = 'product-uploads'
  ),
  1,
  'owner can read own storage object'
);

select throws_ok(
  $$update public.render_jobs
    set attempt_count = 1
    where id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'$$,
  '42501',
  null,
  'browser role cannot alter worker-owned attempt count'
);

select set_config('request.jwt.claim.sub', '22222222-2222-2222-2222-222222222222', true);
select is(
  (select count(*)::int from public.projects),
  0,
  'cross-user project read is denied'
);
select throws_ok(
  $$insert into public.projects (user_id, name)
    values ('11111111-1111-1111-1111-111111111111', 'forged')$$,
  '42501',
  null,
  'cross-user project insert is denied'
);
select throws_ok(
  $$insert into public.assets (project_id, user_id, kind, bucket, object_path, mime_type, byte_size)
    values (
      'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      '22222222-2222-2222-2222-222222222222',
      'source_front',
      'product-uploads',
      '22222222-2222-2222-2222-222222222222/x.png',
      'image/png',
      12
    )$$,
  '42501',
  null,
  'cross-user project asset insert is denied'
);
select is(
  (
    select count(*)::int
    from storage.objects
    where bucket_id = 'product-uploads'
  ),
  0,
  'cross-user storage read is denied'
);
select throws_ok(
  $$insert into storage.objects (bucket_id, name, owner_id, metadata)
    values (
      'product-uploads',
      '11111111-1111-1111-1111-111111111111/forged.png',
      '22222222-2222-2222-2222-222222222222',
      '{}'::jsonb
    )$$,
  '42501',
  null,
  'cross-user storage insert is denied'
);

reset role;
select is(
  (select public from storage.buckets where id = 'product-uploads'),
  false,
  'upload bucket is private'
);
select is(
  (select public from storage.buckets where id = 'product-outputs'),
  false,
  'output bucket is private'
);
select is(
  (select count(*)::int from storage.buckets where id = 'product-twin-assets'),
  0,
  'obsolete prototype bucket is absent'
);
select ok(
  not exists (
    select 1
    from pg_policies
    where coalesce(qual, '') like '%auth.role%'
       or coalesce(with_check, '') like '%auth.role%'
  ),
  'no policy relies on deprecated auth.role'
);
select is(
  (
    select count(*)::int
    from pg_class
    where relname in ('projects', 'assets', 'packaging_specs', 'render_jobs')
      and relrowsecurity
  ),
  4,
  'RLS is enabled on every exposed table'
);
select ok(
  not (
    select prosecdef
    from pg_proc
    where oid = 'public.claim_render_job(uuid,text)'::regprocedure
  ),
  'claim function is security invoker'
);
select is(
  (
    select has_function_privilege(
      'authenticated',
      'public.claim_render_job(uuid,text)',
      'EXECUTE'
    )
  ),
  false,
  'authenticated cannot claim jobs'
);
select is(
  (
    select has_function_privilege(
      'service_role',
      'public.claim_render_job(uuid,text)',
      'EXECUTE'
    )
  ),
  true,
  'service role can claim jobs'
);

set local role service_role;
select is(
  (
    select count(*)::int
    from public.claim_render_job(
      'dddddddd-dddd-dddd-dddd-dddddddddddd',
      'worker-a'
    )
  ),
  1,
  'first worker atomically claims queued job'
);
select is(
  (
    select status || ':' || attempt_count::text
    from public.render_jobs
    where id = 'dddddddd-dddd-dddd-dddd-dddddddddddd'
  ),
  'rendering:1',
  'first claim records rendering state and attempt'
);
select is(
  (
    select count(*)::int
    from public.claim_render_job(
      'dddddddd-dddd-dddd-dddd-dddddddddddd',
      'worker-b'
    )
  ),
  0,
  'fresh lock blocks a duplicate worker claim'
);

update public.render_jobs
set locked_at = now() - interval '16 minutes'
where id = 'dddddddd-dddd-dddd-dddd-dddddddddddd';
select is(
  (
    select attempt_count
    from public.claim_render_job(
      'dddddddd-dddd-dddd-dddd-dddddddddddd',
      'worker-b'
    )
  ),
  2,
  'stale lock recovery performs second claim'
);

update public.render_jobs
set locked_at = now() - interval '16 minutes'
where id = 'dddddddd-dddd-dddd-dddd-dddddddddddd';
select is(
  (
    select attempt_count
    from public.claim_render_job(
      'dddddddd-dddd-dddd-dddd-dddddddddddd',
      'worker-c'
    )
  ),
  3,
  'stale lock recovery permits final bounded claim'
);

update public.render_jobs
set locked_at = now() - interval '16 minutes'
where id = 'dddddddd-dddd-dddd-dddd-dddddddddddd';
select is(
  (
    select count(*)::int
    from public.claim_render_job(
      'dddddddd-dddd-dddd-dddd-dddddddddddd',
      'worker-d'
    )
  ),
  0,
  'attempt cap blocks fourth claim'
);

select * from finish();
rollback;
