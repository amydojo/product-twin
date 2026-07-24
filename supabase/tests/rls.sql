begin;
select plan(12);
insert into auth.users(id,aud,role,email,created_at,updated_at) values
('11111111-1111-1111-1111-111111111111','authenticated','authenticated','a@example.test',now(),now()),
('22222222-2222-2222-2222-222222222222','authenticated','authenticated','b@example.test',now(),now());
set local role authenticated;select set_config('request.jwt.claim.sub','11111111-1111-1111-1111-111111111111',true);
insert into public.projects(id,user_id,name) values('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','11111111-1111-1111-1111-111111111111','A');
select is((select count(*)::int from public.projects),1,'owner can read own project');
select throws_ok($$update public.projects set user_id='22222222-2222-2222-2222-222222222222' where id='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'$$,'42501',null,'owner cannot reassign ownership');
select set_config('request.jwt.claim.sub','22222222-2222-2222-2222-222222222222',true);
select is((select count(*)::int from public.projects),0,'cross-user project read denied');
select throws_ok($$insert into public.projects(user_id,name) values('11111111-1111-1111-1111-111111111111','forged')$$,'42501',null,'cross-user project insert denied');
select throws_ok($$insert into public.assets(project_id,user_id,kind,bucket,object_path,mime_type,byte_size) values('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','22222222-2222-2222-2222-222222222222','source_front','product-uploads','22222222-2222-2222-2222-222222222222/x.png','image/png',12)$$,'42501',null,'cross-user project asset insert denied');
select is((select public from storage.buckets where id='product-uploads'),false,'upload bucket is private');
select is((select public from storage.buckets where id='product-outputs'),false,'output bucket is private');
select ok(not exists(select 1 from pg_policies where coalesce(qual,'') like '%auth.role%'),'no auth.role in policies');
select is((select count(*)::int from pg_class where relname in('projects','assets','packaging_specs','render_jobs') and relrowsecurity),4,'RLS enabled on every exposed table');
select ok(not(select prosecdef from pg_proc where proname='claim_render_job'),'claim function is security invoker');
select is((select has_function_privilege('authenticated','public.claim_render_job(uuid,text)','EXECUTE')),false,'authenticated cannot claim jobs');
select is((select has_function_privilege('service_role','public.claim_render_job(uuid,text)','EXECUTE')),true,'service role can claim jobs');
select * from finish();rollback;
