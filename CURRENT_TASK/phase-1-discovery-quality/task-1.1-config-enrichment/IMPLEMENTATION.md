# Task 1.1: Config-Based Profile Enrichment — Implementation Guide

## Поточний стан

```python
# orchestrator.py — configs збираються але ігноруються
def _build_profile_deterministic(
    platform_data: PlatformData,
    ci_insights: CIInsights,
    _configs: tuple[ConfigContent, ...],  # ← UNUSED
) -> ProjectProfile:
    ac = _build_automated_checks(ci_insights)
    guidance = _build_review_guidance(ci_insights)
    gaps = _detect_gaps(ci_insights)
    return ProjectProfile(
        platform_data=platform_data,
        ci_insights=ci_insights,
        language_version=...,
        package_manager=...,
        automated_checks=ac,
        guidance=guidance,
        gaps=gaps,
        # framework=None, layout=None — порожні!
    )
```

## Що створити

### 1. Новий модуль `discovery/config_parser.py`

Чисті функції для витягування structured data з config content.

```python
"""Deterministic extraction of framework, layout, conventions from config files.

Zero LLM tokens: regex/keyword matching on already-collected config content.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_reviewer.discovery.config_collector import ConfigContent
    from ai_reviewer.discovery.models import PlatformData

# ── Framework detection ──────────────────────────────────────────

# pyproject.toml: [project] dependencies = ["django>=4.2"]
# package.json: "dependencies": {"react": "^18.0"}
# go.mod: require github.com/gin-gonic/gin v1.9
# Cargo.toml: [dependencies] actix-web = "4"

PYTHON_FRAMEWORKS: dict[str, str] = {
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "starlette": "Starlette",
    "tornado": "Tornado",
    "aiohttp": "aiohttp",
    "sanic": "Sanic",
    "litestar": "Litestar",
    "celery": "Celery",  # not a web framework but important context
}

JS_FRAMEWORKS: dict[str, str] = {
    "react": "React",
    "next": "Next.js",
    "vue": "Vue.js",
    "nuxt": "Nuxt",
    "angular": "Angular",     # @angular/core
    "svelte": "Svelte",
    "express": "Express",
    "nestjs": "NestJS",       # @nestjs/core
    "fastify": "Fastify",
}

GO_FRAMEWORKS: dict[str, str] = {
    "gin-gonic/gin": "Gin",
    "labstack/echo": "Echo",
    "gofiber/fiber": "Fiber",
    "gorilla/mux": "Gorilla Mux",
}


def detect_framework(configs: tuple[ConfigContent, ...]) -> str | None:
    """Detect framework from config file contents."""
    for cfg in configs:
        if cfg.path == "pyproject.toml":
            return _detect_python_framework(cfg.content)
        if cfg.path == "package.json":
            return _detect_js_framework(cfg.content)
        if cfg.path == "go.mod":
            return _detect_go_framework(cfg.content)
        if cfg.path == "Cargo.toml":
            return _detect_rust_framework(cfg.content)
    return None
```

**Важливо:** Порядок пріоритету при множинних configs — перевіряти ВСІ і вибирати перший match. Один проєкт може мати і pyproject.toml і package.json (fullstack).

**Парсинг pyproject.toml:**
```python
def _detect_python_framework(content: str) -> str | None:
    """Detect Python framework from pyproject.toml content.

    Scans [project].dependencies and [tool.poetry.dependencies] sections.
    Uses simple string matching — no TOML parser needed for this level.
    """
    content_lower = content.lower()
    for key, name in PYTHON_FRAMEWORKS.items():
        # Match: "django>=4.2", 'django', django = "^4.2"
        if key in content_lower:
            return name
    return None
```

**Аналогічно для JS, Go, Rust.**

### 2. Layout detection

```python
# ── Layout detection ─────────────────────────────────────────────

def detect_layout(platform_data: PlatformData) -> str | None:
    """Detect project layout from file tree.

    Returns:
        "src" — if src/ directory exists with source files
        "flat" — if source files at root level
        "monorepo" — if multiple packages/ or apps/ directories
        None — if cannot determine
    """
    tree = platform_data.file_tree

    has_src = any(p.startswith("src/") for p in tree)
    # Monorepo indicators
    has_packages = any(p.startswith("packages/") for p in tree)
    has_apps = any(p.startswith("apps/") for p in tree)
    has_workspaces = any("workspaces" in p for p in tree)

    if has_packages or (has_apps and has_src):
        return "monorepo"
    if has_src:
        return "src"
    # Flat: source files at root (e.g., main.py, app.py without src/)
    root_source = [p for p in tree if "/" not in p and p.endswith((".py", ".js", ".ts", ".go", ".rs"))]
    if root_source:
        return "flat"
    return None
```

### 3. Convention extraction

```python
# ── Convention extraction ────────────────────────────────────────

def extract_conventions(configs: tuple[ConfigContent, ...]) -> tuple[str, ...]:
    """Extract notable conventions from config file rules.

    Looks for settings that a reviewer should know about:
    - Line length limits
    - Strict mode flags
    - Specific enabled/disabled rules
    """
    conventions: list[str] = []

    for cfg in configs:
        conventions.extend(_extract_from_config(cfg))

    return tuple(conventions[:10])  # cap at 10 to avoid prompt bloat


def _extract_from_config(cfg: ConfigContent) -> list[str]:
    """Extract conventions from a single config file."""
    results: list[str] = []
    content = cfg.content

    # ruff / pyproject.toml
    if "line-length" in content:
        match = re.search(r'line-length\s*=\s*(\d+)', content)
        if match:
            results.append(f"Max line length: {match.group(1)}")

    if "target-version" in content:
        match = re.search(r'target-version\s*=\s*["\']([^"\']+)', content)
        if match:
            results.append(f"Target Python: {match.group(1)}")

    # mypy strict
    if cfg.path in ("mypy.ini", ".mypy.ini", "pyproject.toml"):
        if "strict = true" in content.lower() or "strict = True" in content:
            results.append("mypy strict mode enabled")

    # eslint — check for specific presets
    if "eslintrc" in cfg.path or "eslint.config" in cfg.path:
        if "airbnb" in content.lower():
            results.append("ESLint Airbnb preset")
        elif "standard" in content.lower():
            results.append("ESLint Standard preset")

    # pytest — check for addopts
    if "addopts" in content:
        if "--strict-markers" in content:
            results.append("pytest strict markers")
        if "--strict-config" in content:
            results.append("pytest strict config")

    return results
```

### 4. Оновити `_build_profile_deterministic()`

```python
# orchestrator.py — змінити

from ai_reviewer.discovery.config_parser import (
    detect_framework,
    detect_layout,
    extract_conventions,
)

def _build_profile_deterministic(
    platform_data: PlatformData,
    ci_insights: CIInsights,
    configs: tuple[ConfigContent, ...],  # ← rename: remove underscore!
) -> ProjectProfile:
    """Build a ProjectProfile from deterministic data only."""
    ac = _build_automated_checks(ci_insights)
    guidance = _build_review_guidance(ci_insights)
    gaps = _detect_gaps(ci_insights)

    # NEW: enrich from configs
    framework = detect_framework(configs)
    layout = detect_layout(platform_data)
    conventions = extract_conventions(configs)

    # Merge conventions into guidance
    if conventions:
        guidance = guidance.model_copy(update={
            "conventions": conventions,
        })

    return ProjectProfile(
        platform_data=platform_data,
        ci_insights=ci_insights,
        language_version=ci_insights.python_version
        or ci_insights.node_version
        or ci_insights.go_version,
        package_manager=ci_insights.package_manager,
        framework=framework,
        layout=layout,
        automated_checks=ac,
        guidance=guidance,
        gaps=gaps,
    )
```

### 5. Tests

Файл: `tests/unit/test_discovery/test_config_parser.py`

```python
class TestDetectFramework:
    def test_django_from_pyproject(self):
        cfg = ConfigContent(path="pyproject.toml", content='dependencies = ["django>=4.2"]', size_chars=30)
        assert detect_framework((cfg,)) == "Django"

    def test_react_from_package_json(self):
        cfg = ConfigContent(path="package.json", content='{"dependencies": {"react": "^18"}}', size_chars=35)
        assert detect_framework((cfg,)) == "React"

    def test_no_framework(self):
        cfg = ConfigContent(path="pyproject.toml", content='[project]\nname = "mylib"', size_chars=20)
        assert detect_framework((cfg,)) is None

    def test_gin_from_go_mod(self):
        cfg = ConfigContent(path="go.mod", content='require github.com/gin-gonic/gin v1.9', size_chars=40)
        assert detect_framework((cfg,)) == "Gin"

class TestDetectLayout:
    def test_src_layout(self):
        pd = PlatformData(languages={"Python": 100}, primary_language="Python",
                          file_tree=("src/app/__init__.py", "src/app/main.py", "pyproject.toml"))
        assert detect_layout(pd) == "src"

    def test_monorepo(self):
        pd = PlatformData(languages={"TypeScript": 100}, primary_language="TypeScript",
                          file_tree=("packages/api/src/index.ts", "packages/web/src/index.ts"))
        assert detect_layout(pd) == "monorepo"

class TestExtractConventions:
    def test_ruff_line_length(self):
        cfg = ConfigContent(path="pyproject.toml", content='[tool.ruff]\nline-length = 120', size_chars=30)
        convs = extract_conventions((cfg,))
        assert "Max line length: 120" in convs

    def test_mypy_strict(self):
        cfg = ConfigContent(path="pyproject.toml", content='[tool.mypy]\nstrict = true', size_chars=25)
        convs = extract_conventions((cfg,))
        assert "mypy strict mode enabled" in convs
```

**Оновити existing test fixtures:** `expected_profile.json` для `modern_python` і `javascript` fixtures мають містити framework/layout.

## Checklist

- [ ] Створити `discovery/config_parser.py` з `detect_framework()`, `detect_layout()`, `extract_conventions()`
- [ ] Оновити `_build_profile_deterministic()` — прибрати underscore, використати configs
- [ ] Оновити `_build_fallback_profile()` — також використати configs (де можливо)
- [ ] Написати unit tests для config_parser
- [ ] Оновити fixture expected_profile.json (modern_python, javascript, go_gitlab)
- [ ] `make check` passes
