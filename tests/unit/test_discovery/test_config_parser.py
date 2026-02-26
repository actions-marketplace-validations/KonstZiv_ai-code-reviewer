"""Tests for discovery.config_parser — framework, layout, convention extraction."""

from __future__ import annotations

import pytest

from ai_reviewer.discovery.config_collector import ConfigContent
from ai_reviewer.discovery.config_parser import (
    detect_framework,
    detect_layout,
    extract_conventions,
)
from ai_reviewer.discovery.models import PlatformData


def _cfg(path: str, content: str) -> ConfigContent:
    """Build a ConfigContent with auto-calculated size."""
    return ConfigContent(path=path, content=content, size_chars=len(content))


def _platform(file_tree: tuple[str, ...]) -> PlatformData:
    """Build a minimal PlatformData for layout tests."""
    return PlatformData(
        languages={"Python": 100.0},
        primary_language="Python",
        file_tree=file_tree,
    )


# ── detect_framework ─────────────────────────────────────────────────


class TestDetectFramework:
    """Framework detection from config files."""

    def test_django_from_pyproject(self) -> None:
        cfg = _cfg("pyproject.toml", 'dependencies = ["django>=4.2", "celery"]')
        assert detect_framework((cfg,)) == "Django"

    def test_fastapi_from_pyproject(self) -> None:
        cfg = _cfg("pyproject.toml", 'dependencies = ["fastapi", "uvicorn"]')
        assert detect_framework((cfg,)) == "FastAPI"

    def test_flask_from_pyproject(self) -> None:
        cfg = _cfg("pyproject.toml", 'dependencies = ["flask>=3.0"]')
        assert detect_framework((cfg,)) == "Flask"

    def test_react_from_package_json(self) -> None:
        cfg = _cfg("package.json", '{"dependencies": {"react": "^18"}}')
        assert detect_framework((cfg,)) == "React"

    def test_nextjs_from_package_json(self) -> None:
        cfg = _cfg("package.json", '{"dependencies": {"next": "^14"}}')
        assert detect_framework((cfg,)) == "Next.js"

    def test_angular_from_package_json(self) -> None:
        cfg = _cfg("package.json", '{"dependencies": {"@angular/core": "^17"}}')
        assert detect_framework((cfg,)) == "Angular"

    def test_nestjs_from_package_json(self) -> None:
        cfg = _cfg("package.json", '{"dependencies": {"@nestjs/core": "^10"}}')
        assert detect_framework((cfg,)) == "NestJS"

    def test_gin_from_go_mod(self) -> None:
        cfg = _cfg("go.mod", "require github.com/gin-gonic/gin v1.9")
        assert detect_framework((cfg,)) == "Gin"

    def test_echo_from_go_mod(self) -> None:
        cfg = _cfg("go.mod", "require github.com/labstack/echo/v4 v4.11")
        assert detect_framework((cfg,)) == "Echo"

    def test_actix_from_cargo_toml(self) -> None:
        cfg = _cfg("Cargo.toml", '[dependencies]\nactix-web = "4"')
        assert detect_framework((cfg,)) == "Actix Web"

    def test_axum_from_cargo_toml(self) -> None:
        cfg = _cfg("Cargo.toml", '[dependencies]\naxum = "0.7"')
        assert detect_framework((cfg,)) == "Axum"

    def test_no_framework(self) -> None:
        cfg = _cfg("pyproject.toml", '[project]\nname = "mylib"')
        assert detect_framework((cfg,)) is None

    def test_empty_configs(self) -> None:
        assert detect_framework(()) is None

    def test_unrecognized_config_file(self) -> None:
        cfg = _cfg("Makefile", "all: build")
        assert detect_framework((cfg,)) is None

    def test_first_config_wins(self) -> None:
        """When multiple configs match, the first one wins."""
        py = _cfg("pyproject.toml", 'dependencies = ["django"]')
        js = _cfg("package.json", '{"dependencies": {"react": "^18"}}')
        assert detect_framework((py, js)) == "Django"

    def test_skips_non_matching_then_finds_match(self) -> None:
        """If first config has no framework, continues to next."""
        py = _cfg("pyproject.toml", '[project]\nname = "mylib"')
        js = _cfg("package.json", '{"dependencies": {"vue": "^3"}}')
        assert detect_framework((py, js)) == "Vue.js"


# ── detect_layout ────────────────────────────────────────────────────


class TestDetectLayout:
    """Layout detection from file tree."""

    def test_src_layout(self) -> None:
        pd = _platform(("src/app/__init__.py", "src/app/main.py", "pyproject.toml"))
        assert detect_layout(pd) == "src"

    def test_flat_layout(self) -> None:
        pd = _platform(("main.py", "utils.py", "pyproject.toml"))
        assert detect_layout(pd) == "flat"

    def test_monorepo_packages(self) -> None:
        pd = _platform(("packages/api/src/index.ts", "packages/web/src/index.ts"))
        assert detect_layout(pd) == "monorepo"

    def test_monorepo_apps_and_src(self) -> None:
        pd = _platform(("apps/web/index.ts", "src/shared/utils.ts"))
        assert detect_layout(pd) == "monorepo"

    def test_apps_only_without_src_not_monorepo(self) -> None:
        """apps/ alone without src/ is not monorepo — could be a Django convention."""
        pd = _platform(("apps/users/models.py", "manage.py"))
        assert detect_layout(pd) == "flat"

    def test_no_layout_detected(self) -> None:
        pd = _platform(("README.md", "LICENSE"))
        assert detect_layout(pd) is None

    def test_empty_tree(self) -> None:
        pd = _platform(())
        assert detect_layout(pd) is None

    def test_go_flat_layout(self) -> None:
        pd = _platform(("main.go", "handler.go", "go.mod"))
        assert detect_layout(pd) == "flat"

    def test_rust_src_layout(self) -> None:
        pd = _platform(("src/main.rs", "src/lib.rs", "Cargo.toml"))
        assert detect_layout(pd) == "src"


# ── extract_conventions ──────────────────────────────────────────────


class TestExtractConventions:
    """Convention extraction from config contents."""

    def test_ruff_line_length(self) -> None:
        cfg = _cfg("pyproject.toml", "[tool.ruff]\nline-length = 120")
        convs = extract_conventions((cfg,))
        assert "Max line length: 120" in convs

    def test_ruff_target_version(self) -> None:
        cfg = _cfg("pyproject.toml", '[tool.ruff]\ntarget-version = "py312"')
        convs = extract_conventions((cfg,))
        assert "Target Python: py312" in convs

    def test_mypy_strict(self) -> None:
        cfg = _cfg("pyproject.toml", "[tool.mypy]\nstrict = true")
        convs = extract_conventions((cfg,))
        assert "mypy strict mode enabled" in convs

    def test_mypy_strict_ini(self) -> None:
        cfg = _cfg("mypy.ini", "[mypy]\nstrict = True")
        convs = extract_conventions((cfg,))
        assert "mypy strict mode enabled" in convs

    def test_eslint_airbnb(self) -> None:
        cfg = _cfg(".eslintrc.json", '{"extends": "airbnb"}')
        convs = extract_conventions((cfg,))
        assert "ESLint Airbnb preset" in convs

    def test_eslint_standard(self) -> None:
        cfg = _cfg("eslint.config.js", 'extends: ["standard"]')
        convs = extract_conventions((cfg,))
        assert "ESLint Standard preset" in convs

    def test_pytest_strict_markers(self) -> None:
        cfg = _cfg("pyproject.toml", "[tool.pytest.ini_options]\naddopts = '--strict-markers -v'")
        convs = extract_conventions((cfg,))
        assert "pytest strict markers" in convs

    def test_pytest_strict_config(self) -> None:
        cfg = _cfg("pyproject.toml", "[tool.pytest.ini_options]\naddopts = '--strict-config'")
        convs = extract_conventions((cfg,))
        assert "pytest strict config" in convs

    def test_multiple_conventions_combined(self) -> None:
        content = (
            "[tool.ruff]\nline-length = 88\n\n"
            "[tool.mypy]\nstrict = true\n\n"
            "[tool.pytest.ini_options]\naddopts = '--strict-markers'"
        )
        cfg = _cfg("pyproject.toml", content)
        convs = extract_conventions((cfg,))
        assert len(convs) == 3
        assert "Max line length: 88" in convs
        assert "mypy strict mode enabled" in convs
        assert "pytest strict markers" in convs

    def test_cap_at_10(self) -> None:
        """Conventions are capped at 10 to avoid prompt bloat."""
        # Create content that would match many conventions
        configs = tuple(
            _cfg(".eslintrc.json", f'{{"extends": "airbnb", "rule{i}": true}}') for i in range(15)
        )
        convs = extract_conventions(configs)
        assert len(convs) <= 10

    def test_no_conventions(self) -> None:
        cfg = _cfg("pyproject.toml", '[project]\nname = "mylib"')
        convs = extract_conventions((cfg,))
        assert convs == ()

    def test_empty_configs(self) -> None:
        assert extract_conventions(()) == ()


# ── Integration: detect_framework priority ────────────────────────────


class TestFrameworkPriority:
    """Verify framework detection priority with JS_FRAMEWORKS ordering."""

    def test_nextjs_over_react(self) -> None:
        """Next.js should be detected before React since it includes react."""
        cfg = _cfg("package.json", '{"dependencies": {"next": "^14", "react": "^18"}}')
        assert detect_framework((cfg,)) == "Next.js"

    @pytest.mark.parametrize(
        ("dep", "expected"),
        [
            ("nuxt", "Nuxt"),
            ("svelte", "Svelte"),
            ("fastify", "Fastify"),
        ],
    )
    def test_various_js_frameworks(self, dep: str, expected: str) -> None:
        cfg = _cfg("package.json", f'{{"dependencies": {{"{dep}": "^1"}}}}')
        assert detect_framework((cfg,)) == expected
