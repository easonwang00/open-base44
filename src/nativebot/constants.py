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
SYSTEM_RULES = """You are building an Expo React Native app (SDK 54, React Native 0.81).
The project uses Expo Router for file-based routing. Every file in src/app/ becomes a route.

STACK:
- Expo SDK 54, React Native 0.81, npm (not bun).
- react-native-reanimated v3 for animations.
- react-native-gesture-handler for gestures.
- Use @expo/vector-icons or lucide-react-native for icons.
- All packages must be installed via: npm install

STRUCTURE:
- src/app/          — Expo Router file-based routes (src/app/_layout.tsx is root)
- src/app/index.tsx — Home screen (matches '/')
- src/components/   — Reusable UI components
- src/lib/          — Utilities and helpers

RULES:
- Do NOT create README files or markdown documentation. Focus only on functional code.
- Do NOT run expo start, expo export, expo build, eas build, or any expo/eas commands. The system handles building and previewing.
- Do NOT manage git or touch the dev server.
- After finishing code changes, run: npm install
- Make sure all imports resolve correctly and all referenced packages are in package.json.
- Do NOT fetch external data, scrape websites, or run scripts that make HTTP requests. Use realistic hardcoded mock data instead.
- Do NOT create or run helper scripts (like fetch-*.js). Put all data directly in the source code.
- Keep Bash commands short: only npm install, file operations. No long-running processes.
- Use StyleSheet.create() for styling (no NativeWind/Tailwind).
- Use Pressable over TouchableOpacity.
- Explicit type annotations for useState: `useState<Type[]>([])` not `useState([])`
- Empty strings are text nodes in RN — use `null` not `''` in ternaries.
- Always seed the app with realistic mock data so it looks polished on first launch.
- Populate screens with 5-15 realistic entries.
- For images, use URLs from picsum.photos or unsplash.

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
