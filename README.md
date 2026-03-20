<div align="center">

<img src="assets/nativebot.png" alt="NativeBot" width="120" />

# NativeBot

**Build and ship mobile apps from your terminal. Powered by AI.**

Describe your app → Claude builds it → Preview on your phone → Submit to App Store.

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/nativebot)](https://pypi.org/project/nativebot)
[![GitHub Stars](https://img.shields.io/github/stars/easonwang00/nativebot?style=social)](https://github.com/easonwang00/nativebot)

</div>

---

## Quick Start

```bash
pipx install nativebot   # or: pip install nativebot
claude login
nativebot
```

That's it. Three commands. No API key setup. Uses your Claude subscription.

---

## Demo

```
$ nativebot

  🚀 NativeBot — AI App Builder

  ? What would you like to do? Create new project
  ? Project name: FitnessApp
  ? Describe your app: A fitness tracker with workout logging
  ? Start building now? Yes
  ? Choose model: Sonnet 4.6 (recommended)

  🤖 Claude is working...
  ├─ Reading package.json
  ├─ Writing app/screens/WorkoutScreen.tsx
  ├─ Writing app/components/ExerciseCard.tsx
  ├─ bash → npm install react-native-chart-kit
  ├─ Writing app/screens/ProgressScreen.tsx
  └─ bash → npx expo export -p web

  ✅ Done! 8 files changed in 32s

  You: Add a dark mode toggle to the settings page

  🤖 Claude is working...
  ├─ Reading app/screens/SettingsScreen.tsx
  ├─ Writing app/context/ThemeContext.tsx
  ├─ Edit app/screens/SettingsScreen.tsx
  └─ Edit app/_layout.tsx

  ✅ Done! 3 files changed in 18s
```

## Commands

```bash
nativebot                  # Interactive mode (recommended)
nativebot create "MyApp"   # Create a new project
nativebot list             # List all projects
nativebot open MyApp       # Open project and chat with Claude
nativebot preview MyApp    # Launch Expo dev server
nativebot files MyApp      # Show project file tree
nativebot export MyApp     # Build & submit instructions
nativebot delete MyApp     # Delete a project
```

## Telegram Bot

Build apps from your phone — chat with NativeBot on Telegram.

```bash
pipx install nativebot[telegram]

# 1. Message @BotFather on Telegram → /newbot → copy token
# 2. Start the bot
export TELEGRAM_BOT_TOKEN=your-token
nativebot telegram
```

**Commands in Telegram:**
- `/create MyApp` — Create a new project
- `/open MyApp` — Switch to a project
- `/preview` — Get Expo URL to open on your phone
- `/list` — List all projects
- `/files` — Show file tree
- `/model opus` — Switch model
- Just send a message to chat with Claude!

The bot runs on your machine — same local projects, same `~/.nativebot/projects/` directory.

## How It Works

1. **Create** — Seeds a production-ready Expo React Native template
2. **Chat** — Describe features in plain English, Claude writes the code
3. **Preview** — Run `nativebot preview MyApp` → scan QR with Expo Go on your phone
4. **Iterate** — Keep chatting to add features, fix bugs, refine UI
5. **Ship** — Build with EAS and submit to App Store / Google Play

## Preview Your App

```bash
nativebot preview MyApp
# Opens Expo dev server — scan QR code with Expo Go
```

Or manually:
```bash
cd ~/.nativebot/projects/MyApp
npx expo start
```

## Deploy to App Store

```bash
nativebot export MyApp
# Shows step-by-step build & submit instructions
```

Or directly:
```bash
cd ~/.nativebot/projects/MyApp
npm install -g eas-cli
eas login
eas build --platform ios
eas submit --platform ios
```

## Requirements

| Requirement | Required? | Notes |
|------------|-----------|-------|
| Python 3.10+ | Yes | `python3 --version` |
| Node.js 18+ | Yes | For Expo projects |
| Claude subscription | Recommended | Just run `claude login` — no API key needed |
| Anthropic API Key | Alternative | [Get one](https://console.anthropic.com) if you prefer API access |
| Expo Go (mobile) | Recommended | For live preview on phone |
| Apple Developer Account | For shipping | For App Store submission |

## Architecture

```
You (terminal)          NativeBot CLI            Claude Agent SDK
┌──────────────┐    ┌────────────────┐    ┌──────────────────┐
│ nativebot open   │───▶│ Project Manager │───▶│ Claude AI         │
│ "Add login"   │◀───│ Chat Session    │◀───│ Reads/Writes code │
└──────────────┘    └────────────────┘    └──────────────────┘
                           │
                    ~/.nativebot/projects/
                    ├── FitnessApp/
                    │   ├── app/
                    │   ├── package.json
                    │   └── .nativebot/conversation.json
                    └── TodoApp/
```

- Projects are real directories on your filesystem
- Claude edits files directly — no database, no cloud sync
- Conversations saved locally for session continuity
- Your code, your machine, your control

## Why NativeBot?

| | Replit | Bolt | Lovable | Vibecode | **NativeBot** |
|--|--------|------|---------|----------|------------|
| Open source | ❌ | ❌ | ❌ | ❌ | ✅ |
| CLI / Terminal | ❌ | ❌ | ❌ | ❌ | ✅ |
| Self-hosted | ❌ | ❌ | ❌ | ❌ | ✅ |
| Your own API key | ❌ | ❌ | ❌ | ❌ | ✅ |
| Mobile-first (Expo) | ❌ | ❌ | ❌ | ✅ | ✅ |
| No account required | ❌ | ❌ | ❌ | ❌ | ✅ |
| Unlimited usage | ❌ | ❌ | ❌ | ❌ | ✅ |
| Free forever | ❌ | ❌ | ❌ | ❌ | ✅ |

## Project Structure

```
nativebot/
├── src/nativebot/
│   ├── cli.py          # Click commands
│   ├── chat.py         # Interactive chat with Claude
│   ├── projects.py     # Project management (filesystem)
│   ├── agent.py        # Claude Agent SDK integration
│   ├── constants.py    # Models, tools, system rules
│   └── display.py      # Rich terminal formatting
├── template/           # Expo seed template
├── pyproject.toml      # Package config
├── README.md
├── VISION.md
└── LICENSE
```

## Configuration

Projects are stored in `~/.nativebot/projects/`. To change:

```bash
export NATIVEBOT_PROJECTS_DIR=/path/to/projects
```

Default model is Claude Sonnet 4.6. To change:

```bash
nativebot open MyApp --model opus    # Use Opus 4.6
nativebot open MyApp --model haiku   # Use Haiku 4.5
```

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
  Built with ❤️ by the NativeBot community<br>
  Powered by <a href="https://anthropic.com">Claude</a> · <a href="https://expo.dev">Expo</a>
</div>
