"""Filesystem-based project management for NativeBot.

Projects live under ~/.nativebot/projects/<project-name>/.
Each project stores metadata in .nativebot/metadata.json and
conversation history in .nativebot/conversation.json.
"""

import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .constants import SKIP_DIRS


def get_mobile_dir(project_dir: Path) -> Path:
    """Get the mobile app directory for npm/expo commands.

    Returns project_dir/mobile/ if it exists (new template),
    otherwise project_dir itself (old flat template).
    """
    mobile = Path(project_dir) / "mobile"
    if mobile.is_dir():
        return mobile
    return Path(project_dir)

# Base directory for all projects
# Uses NATIVEBOT_PROJECTS_DIR env var, or ~/.nativebot/projects/
PROJECTS_BASE = Path(os.environ.get("NATIVEBOT_PROJECTS_DIR", str(Path.home() / ".nativebot" / "projects")))

# Template directory -- look inside the package first (pip/pipx install),
# then fall back to repo root (development mode)
_PACKAGE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PACKAGE_DIR.parent.parent  # src/nativebot -> src -> repo root

_TEMPLATE_CANDIDATES = [
    _PACKAGE_DIR / "template",              # Inside installed package
    _REPO_ROOT / "template" / "expo-app",   # Development: repo root
]

TEMPLATE_DIR: Optional[Path] = None
for _candidate in _TEMPLATE_CANDIDATES:
    if _candidate.is_dir():
        TEMPLATE_DIR = _candidate
        break


def _ensure_base():
    """Create the projects base directory if it doesn't exist."""
    PROJECTS_BASE.mkdir(parents=True, exist_ok=True)


def _slugify(name: str) -> str:
    """Convert a project name to a filesystem-safe slug."""
    slug = name.lower().strip()
    slug = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in slug)
    slug = "-".join(part for part in slug.split("-") if part)  # collapse dashes
    return slug[:100] or "project"


def create_project(name: str, description: str = "") -> Path:
    """Create a new project directory with template files.

    Returns the path to the created project directory.
    Raises ValueError if a project with that name already exists.
    """
    _ensure_base()

    slug = _slugify(name)
    project_dir = PROJECTS_BASE / slug

    if project_dir.exists():
        raise ValueError(
            f"Project '{slug}' already exists at {project_dir}. "
            "Choose a different name or delete the existing project."
        )

    # Copy template if available, otherwise create empty project
    if TEMPLATE_DIR and TEMPLATE_DIR.is_dir():
        shutil.copytree(
            TEMPLATE_DIR,
            project_dir,
            ignore=shutil.ignore_patterns(
"node_modules", "package-lock.json", ".expo", ".git", "__pycache__", ".DS_Store"
            ),
        )
    else:
        project_dir.mkdir(parents=True)

    # Update app.json with the app name (check both root and mobile/)
    for app_json_rel in ["app.json", "mobile/app.json"]:
        app_json_path = project_dir / app_json_rel
        if app_json_path.exists():
            try:
                app_config = json.loads(app_json_path.read_text())
                expo = app_config.get("expo", {})
                expo["name"] = name.strip()
                expo["slug"] = slug
                expo["scheme"] = slug
                app_config["expo"] = expo
                app_json_path.write_text(json.dumps(app_config, indent=2))
            except Exception:
                pass

    # Update package.json name (check both root and mobile/)
    for pkg_json_rel in ["package.json", "mobile/package.json"]:
        pkg_json_path = project_dir / pkg_json_rel
        if pkg_json_path.exists():
            try:
                pkg = json.loads(pkg_json_path.read_text())
                pkg["name"] = slug
                pkg_json_path.write_text(json.dumps(pkg, indent=2))
            except Exception:
                pass

    # Create .nativebot metadata directory
    meta_dir = project_dir / ".nativebot"
    meta_dir.mkdir(exist_ok=True)

    metadata = {
        "id": str(uuid.uuid4()),
        "name": name.strip()[:255],
        "description": description.strip()[:2000],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "slug": slug,
    }
    (meta_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (meta_dir / "conversation.json").write_text("[]")

    return project_dir


def list_projects() -> list[dict]:
    """Scan PROJECTS_BASE and return a list of project info dicts.

    Each dict contains: name, description, created_at, path, file_count, slug.
    Sorted by creation date (newest first).
    """
    _ensure_base()
    projects = []

    for entry in sorted(PROJECTS_BASE.iterdir()):
        if not entry.is_dir():
            continue
        meta = get_metadata(entry)
        if not meta:
            continue
        file_count = len(get_project_files(entry))
        projects.append(
            {
                "name": meta.get("name", entry.name),
                "description": meta.get("description", ""),
                "created_at": meta.get("created_at", ""),
                "path": str(entry),
                "slug": meta.get("slug", entry.name),
                "id": meta.get("id", ""),
                "file_count": file_count,
            }
        )

    # Sort newest first
    projects.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return projects


def get_project(name_or_id: str) -> Optional[dict]:
    """Find a project by name, slug, or UUID.

    Returns project info dict or None.
    """
    _ensure_base()
    query = name_or_id.strip().lower()

    for entry in PROJECTS_BASE.iterdir():
        if not entry.is_dir():
            continue
        meta = get_metadata(entry)
        if not meta:
            continue

        # Match by slug (directory name), name, or UUID
        if (
            entry.name.lower() == query
            or meta.get("name", "").lower() == query
            or meta.get("slug", "").lower() == query
            or meta.get("id", "").lower() == query
        ):
            return {
                "name": meta.get("name", entry.name),
                "description": meta.get("description", ""),
                "created_at": meta.get("created_at", ""),
                "path": str(entry),
                "slug": meta.get("slug", entry.name),
                "id": meta.get("id", ""),
                "file_count": len(get_project_files(entry)),
            }

    return None


def delete_project(name_or_id: str) -> bool:
    """Delete a project by name, slug, or UUID.

    Returns True if deleted, False if not found.
    """
    project = get_project(name_or_id)
    if not project:
        return False

    project_path = Path(project["path"])
    if project_path.exists():
        shutil.rmtree(project_path)
    return True


def get_project_files(project_dir: Path) -> list[str]:
    """Walk the project directory and return relative file paths.

    Skips directories listed in SKIP_DIRS.
    """
    project_dir = Path(project_dir)
    if not project_dir.is_dir():
        return []

    files = []
    for path in sorted(project_dir.rglob("*")):
        if not path.is_file():
            continue
        # Check if any parent directory should be skipped
        rel = path.relative_to(project_dir)
        parts = rel.parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        # Skip hidden files in the root (like .DS_Store) but keep nested ones
        if parts[0].startswith(".") and len(parts) == 1:
            continue
        files.append(str(rel))

    return files


def get_conversation(project_dir: Path) -> list[dict]:
    """Read the conversation history for a project."""
    conv_file = Path(project_dir) / ".nativebot" / "conversation.json"
    if not conv_file.exists():
        return []
    try:
        data = json.loads(conv_file.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_conversation(project_dir: Path, messages: list[dict]):
    """Write the conversation history for a project."""
    meta_dir = Path(project_dir) / ".nativebot"
    meta_dir.mkdir(exist_ok=True)
    conv_file = meta_dir / "conversation.json"
    conv_file.write_text(json.dumps(messages, indent=2, default=str))


def get_metadata(project_dir: Path) -> Optional[dict]:
    """Read project metadata. Returns None if no valid metadata found."""
    meta_file = Path(project_dir) / ".nativebot" / "metadata.json"
    if not meta_file.exists():
        return None
    try:
        data = json.loads(meta_file.read_text())
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None
