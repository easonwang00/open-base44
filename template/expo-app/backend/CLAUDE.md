# NativeBot Backend - Supabase

This is the optional Supabase backend for NativeBot apps.
Only used when the user has configured Supabase credentials.

## Tech Stack

- **Platform**: Supabase (hosted PostgreSQL + Auth + Storage)
- **Client**: @supabase/supabase-js
- **Database**: PostgreSQL via Supabase (multi-tenant with RLS)
- **Auth**: Supabase Auth (email/password + OAuth)
- **Storage**: Supabase Storage (per-app folders)
- **Server Logic**: Supabase Edge Functions (Deno) — only when needed

## Architecture

- Single Supabase project serves the app
- Every data table has `app_id` column for tenant isolation
- Row Level Security (RLS) enforces that users only access their own data
- Frontend talks directly to Supabase — no middleman server for basic CRUD
- Edge Functions handle server-side logic (validation, privileged ops)

## Environment Variables

- `SUPABASE_URL` — Project URL
- `SUPABASE_ANON_KEY` — Public anon key (safe for frontend)
- `SUPABASE_SERVICE_ROLE_KEY` — Admin key (server-side only, never expose)
