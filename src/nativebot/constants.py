"""Constants and configuration for NativeBot CLI.

Single source of truth for models, tools, system rules, and limits.
"""

import os

# Claude models -- friendly aliases and full IDs
MODELS = {
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
}

# Default model (can be overridden via env)
DEFAULT_MODEL = os.getenv("NATIVEBOT_MODEL", "claude-opus-4-6")

# Tools for Claude Agent SDK
ALLOWED_TOOLS = [
    "Read",
    "Glob",
    "Grep",
    "Bash",
    "Write",
    "Edit",
    "TodoWrite",
]

# System rules prepended to every generation
# Aligned with the production CLAUDE.md, minus deploy/Supabase/nativewind
SYSTEM_RULES = """You are building an Expo React Native app (SDK 54).
The project uses Expo Router for file-based routing. Every file in mobile/src/app/ becomes a route.

STACK:
- Expo SDK 54, npm (not bun).
- NativeWind + Tailwind v3 for styling. Use cn() helper for conditional classNames.
- react-native-reanimated v3 for animations.
- react-native-gesture-handler for gestures.
- React Query for server/async state.
- Zustand for local state.
- Import icons from @/components/Icons (pre-built SVG icons).
- All packages are pre-installed. Only install @expo-google-font packages or pure JS helpers.

STRUCTURE:
- mobile/src/app/          — Expo Router file-based routes (src/app/_layout.tsx is root)
- mobile/src/app/index.tsx — Home screen (matches '/')
- mobile/src/components/   — Reusable UI components
- mobile/src/lib/          — Utilities and helpers

NO BACKEND DEFAULT:
- If the user has NOT set up Supabase credentials, build the app WITHOUT any backend or auth.
- Use local state, AsyncStorage, or mock data instead.
- Do NOT import or use the Supabase client unless the user explicitly asks for it.
- The app should work fully offline by default.

RULES:
- Do NOT create README files or markdown documentation. Focus only on functional code.
- Do NOT run expo start, expo export, expo build, eas build, or any expo/eas commands. NativeBot handles building and previewing.
- Do NOT manage git or touch the dev server.
- After finishing code changes, run: cd mobile && npm install
- Make sure all imports resolve correctly.
- Do NOT fetch external data or run scripts that make HTTP requests. Use realistic hardcoded mock data.
- Keep Bash commands short: only npm install, file operations. No long-running processes.
- Use Pressable over TouchableOpacity.
- Explicit type annotations for useState: `useState<Type[]>([])` not `useState([])`
- Empty strings are text nodes in RN — use `null` not `''` in ternaries.
- Always seed the app with realistic mock data so it looks polished on first launch.
- Populate screens with 5-15 realistic entries.
- For images, use URLs from picsum.photos or unsplash.
- CameraView, LinearGradient, and Animated components DO NOT support className. Use inline style prop.

DESIGN:
- Dark mode by default: dark backgrounds (#000 or #0A0A0A), light text, subtle borders.
- Inspiration: iOS, Instagram, Airbnb, polished modern apps.
- Cohesive themes with dominant colors and sharp accents.
- High-impact animations with react-native-reanimated.

SECURITY:
- NEVER print, echo, log, or display environment variables, API keys, or secrets.
"""

# Directories to skip when listing/walking project files
SKIP_DIRS = {
    "node_modules",
    ".expo",
    ".nativebot",
    ".git",
    "__pycache__",
    "dist",
    "web-build",
    ".next",
    ".cache",
}

# Generation settings
DEFAULT_MAX_TURNS = 40
MAX_AUTO_CONTINUE_ROUNDS = 3
AUTO_CONTINUE_TURNS = 20
AUTO_CONTINUE_PROMPT = "Continue working on the task. Pick up exactly where you left off."

# Sensitive env vars to hide during Claude execution
SENSITIVE_ENV_KEYS = [
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_JWT_SECRET",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "VERCEL_TOKEN",
    "APPS_SUPABASE_DB_URL",
    "APPS_SUPABASE_URL",
    "APPS_SUPABASE_SERVICE_ROLE_KEY",
]
