"""Deterministic extraction of framework, layout, conventions from config files.

Zero LLM tokens: regex/keyword matching on already-collected config content.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_reviewer.discovery.config_collector import ConfigContent
    from ai_reviewer.discovery.models import PlatformData

# ── Framework detection maps ─────────────────────────────────────────

PYTHON_FRAMEWORKS: dict[str, str] = {
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "starlette": "Starlette",
    "tornado": "Tornado",
    "aiohttp": "aiohttp",
    "sanic": "Sanic",
    "litestar": "Litestar",
    "celery": "Celery",
}

JS_FRAMEWORKS: dict[str, str] = {
    "next": "Next.js",
    "@angular/core": "Angular",
    "@nestjs/core": "NestJS",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
    "fastify": "Fastify",
    "vue": "Vue.js",
    "react": "React",
    "express": "Express",
}

GO_FRAMEWORKS: dict[str, str] = {
    "gin-gonic/gin": "Gin",
    "labstack/echo": "Echo",
    "gofiber/fiber": "Fiber",
    "gorilla/mux": "Gorilla Mux",
}

RUST_FRAMEWORKS: dict[str, str] = {
    "actix-web": "Actix Web",
    "axum": "Axum",
    "rocket": "Rocket",
    "warp": "Warp",
}

# ── Source file extensions for flat layout detection ──────────────────

_SOURCE_EXTENSIONS: tuple[str, ...] = (".py", ".js", ".ts", ".go", ".rs", ".java", ".kt")

# Regex for convention extraction
_LINE_LENGTH_RE = re.compile(r"line-length\s*=\s*(\d+)")
_TARGET_VERSION_RE = re.compile(r"target-version\s*=\s*[\"']([^\"']+)")


# ── Framework detection ──────────────────────────────────────────────


def detect_framework(configs: tuple[ConfigContent, ...]) -> str | None:
    """Detect the primary framework from config file contents.

    Checks all configs and returns the first match. Priority is given by
    the order of configs (typically: pyproject.toml, package.json, go.mod,
    Cargo.toml).
    """
    for cfg in configs:
        result: str | None = None
        if cfg.path == "pyproject.toml":
            result = _detect_python_framework(cfg.content)
        elif cfg.path == "package.json":
            result = _detect_js_framework(cfg.content)
        elif cfg.path == "go.mod":
            result = _detect_go_framework(cfg.content)
        elif cfg.path == "Cargo.toml":
            result = _detect_rust_framework(cfg.content)
        if result is not None:
            return result
    return None


def _detect_python_framework(content: str) -> str | None:
    """Detect Python framework from pyproject.toml content.

    Scans [project].dependencies and [tool.poetry.dependencies] sections.
    Uses simple string matching — no TOML parser needed for this level.
    """
    content_lower = content.lower()
    for key, name in PYTHON_FRAMEWORKS.items():
        if key in content_lower:
            return name
    return None


def _detect_js_framework(content: str) -> str | None:
    """Detect JS/TS framework from package.json content."""
    content_lower = content.lower()
    for key, name in JS_FRAMEWORKS.items():
        if key in content_lower:
            return name
    return None


def _detect_go_framework(content: str) -> str | None:
    """Detect Go framework from go.mod content."""
    for key, name in GO_FRAMEWORKS.items():
        if key in content:
            return name
    return None


def _detect_rust_framework(content: str) -> str | None:
    """Detect Rust framework from Cargo.toml content."""
    content_lower = content.lower()
    for key, name in RUST_FRAMEWORKS.items():
        if key in content_lower:
            return name
    return None


# ── Layout detection ─────────────────────────────────────────────────


def detect_layout(platform_data: PlatformData) -> str | None:
    """Detect project layout from file tree.

    Returns:
        "src" — if src/ directory exists with source files.
        "flat" — if source files at root level.
        "monorepo" — if packages/ or multiple apps/ directories.
        None — if cannot determine.
    """
    tree = platform_data.file_tree

    has_src = any(p.startswith("src/") for p in tree)
    has_packages = any(p.startswith("packages/") for p in tree)
    has_apps = any(p.startswith("apps/") for p in tree)

    if has_packages or (has_apps and has_src):
        return "monorepo"
    if has_src:
        return "src"

    root_source = [p for p in tree if "/" not in p and p.endswith(_SOURCE_EXTENSIONS)]
    if root_source:
        return "flat"
    return None


# ── Convention extraction ────────────────────────────────────────────


def extract_conventions(configs: tuple[ConfigContent, ...]) -> tuple[str, ...]:
    """Extract notable conventions from config file rules.

    Looks for settings that a reviewer should know about:
    - Line length limits
    - Strict mode flags
    - Specific enabled/disabled rules

    Returns at most 10 conventions to avoid prompt bloat.
    """
    conventions: list[str] = []

    for cfg in configs:
        conventions.extend(_extract_from_config(cfg))

    return tuple(conventions[:10])


def _extract_from_config(cfg: ConfigContent) -> list[str]:
    """Extract conventions from a single config file."""
    results: list[str] = []
    content = cfg.content

    # ruff / pyproject.toml — line-length
    match = _LINE_LENGTH_RE.search(content)
    if match:
        results.append(f"Max line length: {match.group(1)}")

    # ruff / pyproject.toml — target-version
    match = _TARGET_VERSION_RE.search(content)
    if match:
        results.append(f"Target Python: {match.group(1)}")

    # mypy strict
    _mypy_paths = ("mypy.ini", ".mypy.ini", "pyproject.toml", "setup.cfg")
    if cfg.path in _mypy_paths and "strict = true" in content.lower():
        results.append("mypy strict mode enabled")

    # eslint presets
    if "eslintrc" in cfg.path or "eslint.config" in cfg.path:
        content_lower = content.lower()
        if "airbnb" in content_lower:
            results.append("ESLint Airbnb preset")
        elif "standard" in content_lower:
            results.append("ESLint Standard preset")

    # pytest addopts
    if "addopts" in content:
        if "--strict-markers" in content:
            results.append("pytest strict markers")
        if "--strict-config" in content:
            results.append("pytest strict config")

    return results


__all__ = [
    "GO_FRAMEWORKS",
    "JS_FRAMEWORKS",
    "PYTHON_FRAMEWORKS",
    "RUST_FRAMEWORKS",
    "detect_framework",
    "detect_layout",
    "extract_conventions",
]
