-- Cover foreign keys used by cascades and owner-scoped access paths.
create index assets_user_idx on public.assets(user_id);
create index packaging_specs_user_idx on public.packaging_specs(user_id);
create index render_jobs_project_idx on public.render_jobs(project_id);
create index render_jobs_user_idx on public.render_jobs(user_id);
