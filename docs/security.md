# Security model

## Identity and ownership

Anonymous Supabase authentication is still authentication: each session receives a stable user UUID. Every user-owned table stores that UUID, enables RLS, and uses `(select auth.uid()) = user_id`. `auth.role()` is never used. Foreign-key-aware policies prevent a user from attaching assets, specifications, or jobs to another user's project.

## Private object storage

`product-uploads` and `product-outputs` are private. Object paths are user-prefixed and storage policies compare the first folder to `auth.uid()`. The UI reads and downloads through short-lived signed URLs. Public object URLs are not used.

## Service-role isolation

Only the worker receives `SUPABASE_SERVICE_ROLE_KEY`. It is never named with `NEXT_PUBLIC_`, committed, returned by an endpoint, included in a manifest, or printed by the debug route. The browser and Next.js user operations use the publishable key and remain subject to RLS.

## Worker authentication

Mutation endpoints require an HMAC-SHA256 signature over:

```text
HTTP method
request path
Unix timestamp
single-use random nonce
SHA-256 body digest
```

The worker requires at least 32 secret bytes, accepts a five-minute clock window, uses constant-time comparison, and rejects a nonce after its first valid use through a bounded in-memory replay guard. The atomic database claim remains the durable protection against duplicate job execution. Job IDs are parsed as UUIDs before processing.

## Upload validation

The browser provides convenience checks, but the Next.js server is authoritative. Front photos and label artwork are limited to PNG, JPEG, or WebP and 15 MB. The server checks the file signature against the declared MIME type, derives object extensions from that type, and normalizes the original filename before retaining it as display-only metadata. User filenames never become storage paths. Supabase buckets enforce an additional MIME and byte limit.

## Subprocess safety

The worker creates a unique temporary directory, validates every owned object path, downloads only known asset kinds, writes the approved specification to a fixed local filename, and calls Blender with a fixed script and argument array. It does not accept arbitrary shell commands, file paths, Blender scripts, Python code, or remote model code from a request.

## Model safety

Model adapters are lazy and revision-pinned. Normal CI and deterministic fixture mode never download weights. BiRefNet custom code is isolated behind an optional provider and is not silently enabled because its repository lacks a clear license declaration. Provider failure is recorded before a no-op fallback is used.

## Debug surface

The debug route is unavailable in production unless `ENABLE_DEBUG_VIEW=true`. It may show owned database records, validation output, safe command templates, masks, manifests, and output metadata. It never renders environment variables, authorization headers, service-role values, HMAC secrets, Hugging Face tokens, or absolute worker filesystem paths. Public API failures return stable messages rather than raw provider/database errors.

## Verification

`supabase/tests/rls.sql` proves owner and cross-user table/storage behavior, private buckets, RLS on every exposed table, the absence of `auth.role()`, browser denial of worker-owned job columns, atomic claiming, stale-lock recovery, and the three-attempt cap. `scripts/scan_secrets.py` fails CI on common committed-secret patterns.
