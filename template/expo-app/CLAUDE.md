# NativeBot Workspace

This workspace contains a mobile app with an optional Supabase backend.

<projects>
  mobile/   — Expo React Native app (port 8081)
  backend/  — Supabase backend (optional — only if user sets up Supabase credentials)
</projects>

<environment_variables>
Mobile (in mobile/src/*.ts):

- Use `process.env.EXPO_PUBLIC_SUPABASE_URL` and `process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY` for Supabase
- EXPO_PUBLIC_* vars are bundled at build time
- For most CRUD: talk directly to Supabase from the frontend using the client SDK

Backend (in backend/src/*.ts) — only if Supabase is configured:

- Use `env` from "./env" (validated via Zod) for backend env vars
- SUPABASE_SERVICE_ROLE_KEY is admin-only — never expose to frontend
</environment_variables>

<no_backend_default>
  IMPORTANT: If the user has NOT set up Supabase credentials (no EXPO_PUBLIC_SUPABASE_URL in .env),
  build the app WITHOUT any backend or auth. Use local state, AsyncStorage, or mock data instead.
  Do NOT import or use the Supabase client unless the user explicitly asks for Supabase/auth/database.
  The app should work fully offline by default.
</no_backend_default>

<supabase>
  Only applies when user has set up Supabase credentials via the `env` command.

  Supabase env vars (EXPO_PUBLIC_SUPABASE_URL, EXPO_PUBLIC_SUPABASE_ANON_KEY) are loaded from .env.
  The mobile app has a pre-configured client at `mobile/src/lib/supabase.ts`.

Architecture:

- Frontend talks directly to Supabase for basic CRUD (no middleman server needed)
- Edge Functions (Deno) handle server-side logic when needed (validation, privileged ops)
- Every data table MUST have `app_id TEXT NOT NULL` for tenant isolation
- RLS enforces data boundaries even if frontend forgets to filter by app_id
</supabase>

<rules>
  GENERAL:
  - Do NOT create README files or any markdown documentation files. Focus only on functional code.
  - Communicate concisely. Don't talk too much.

ICONS:

- Import icons from `@/components/Icons` (pre-built SVG icons that work on all platforms).
- Available: HomeIcon, SearchIcon, PlusIcon, XIcon, SettingsIcon, UserIcon, HeartIcon, StarIcon, ChevronLeftIcon, ChevronRightIcon, ChevronDownIcon, ChevronUpIcon, CheckIcon, TrashIcon, EditIcon, MenuIcon, BellIcon, CalendarIcon, ClockIcon, MailIcon, LockIcon, EyeIcon, EyeOffIcon, ArrowLeftIcon, ArrowRightIcon, LogOutIcon
- All icons accept `size` and `color` props: `<HomeIcon size={24} color="#fff" />`
- If you need an icon not in the set, add it to `@/components/Icons` using the same SVG pattern.
- @expo/vector-icons is also available as a fallback.

SECURITY:

- NEVER print, echo, log, or display environment variables, API keys, tokens, secrets, or credentials.
- Do NOT run: env, printenv, cat .env, echo $TOKEN, or any command that reveals secret values.

PREVIEW:

- The app is previewed on the user's phone via Expo Go (npx expo start).
- NativeBot handles starting and stopping the preview server.
- Do NOT run expo start, expo export, expo build, eas build, or any expo/eas commands.
- After finishing code changes, run: npm install

BUILD:

1. cd mobile && npm install
2. NativeBot handles preview and builds — do NOT run expo commands yourself.

DARK MODE DEFAULT:

- Dark backgrounds: #000000 or #0A0A0A
- Light text: white or rgba(255,255,255,0.9)
- Subtle borders: rgba(255,255,255,0.15)
- Accent gradient: linear-gradient(135deg, #69B3FF 0%, #FF9CF5 50%, #EBCFAC 100%)
- Cards/surfaces: translucent dark fills (rgba(255,255,255,0.08))
- Aesthetic: sleek, modern, dark-first.

ERROR HANDLING:

- Do NOT add global error overlays, error popups, or visible error handlers.
- Handle errors silently with try/catch and console.log only.
- The app should never display raw error messages to the user.

DUMMY DATA:

- Always seed the app with realistic mock data so it looks polished on first launch.
- Populate screens with 5–15 realistic entries (sample conversations, posts, products, etc.).
- Use picsum.photos or unsplash URLs for placeholder images.
- The app should never look empty on first open.

AUTH (only when using Supabase Auth — skip if no Supabase credentials):

- Use a SINGLE "Continue" button (NOT separate Sign In / Sign Up).
- Try signUp() first; if user already exists, fall back to signInWithPassword().
- One screen, one button.
</rules>

<environment>
  NativeBot manages the dev server and builds. DO NOT manage these.
  The user previews the app on their phone via Expo Go.
  Do NOT tell the user to run expo start or any dev server commands.
</environment>
