# NativeBot App Template

Starter template for NativeBot apps.

## Structure

```
mobile/     — Expo React Native app
backend/    — Supabase backend (optional)
```

## Mobile App

- Expo SDK 54 with React Native
- NativeWind (TailwindCSS) for styling
- React Query for data fetching
- Zustand for state management
- Supabase JS SDK for auth, database, and storage (optional)

## Backend (Optional)

Only needed if you set up Supabase credentials via `nativebot` → `env` command.

- Supabase (PostgreSQL + Auth + Storage)
- Row Level Security (RLS) for per-user data isolation
- SQL migrations in `backend/supabase/migrations/`

## Getting Started

```bash
nativebot
```

No Supabase? No problem — the app works fully offline with local state and mock data.
