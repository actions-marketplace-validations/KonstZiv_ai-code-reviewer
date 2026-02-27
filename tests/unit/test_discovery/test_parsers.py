"""Tests for discovery.parsers — file classification, package managers, layout."""

from __future__ import annotations

import pytest

from ai_reviewer.discovery.parsers import (
    FILE_TREE_LIMIT,
    check_file_tree_truncation,
    classify_collected_files,
    detect_layout,
    detect_package_managers,
    sanitize_secrets,
)

# ── classify_collected_files ──────────────────────────────────────────


class TestClassifyCollectedFiles:
    """Split collected configs into dep / config / CI categories."""

    def test_pyproject_goes_to_both_dep_and_config(self) -> None:
        configs = {"pyproject.toml": "[project]\nname='test'"}
        deps, cfgs, _ci = classify_collected_files(configs)
        assert "pyproject.toml" in deps
        assert "pyproject.toml" in cfgs

    def test_package_json_is_dependency(self) -> None:
        configs = {"package.json": '{"name": "app"}'}
        deps, cfgs, _ci = classify_collected_files(configs)
        assert "package.json" in deps
        assert "package.json" not in cfgs

    def test_ruff_toml_is_config(self) -> None:
        configs = {"ruff.toml": "line-length = 100"}
        deps, cfgs, _ci = classify_collected_files(configs)
        assert "ruff.toml" not in deps
        assert "ruff.toml" in cfgs

    def test_ci_workflow_classified(self) -> None:
        configs = {".github/workflows/ci.yml": "name: CI"}
        _deps, _cfgs, ci = classify_collected_files(configs)
        assert ".github/workflows/ci.yml" in ci

    def test_gitlab_ci_classified(self) -> None:
        configs = {".gitlab-ci.yml": "stages: [test]"}
        _deps, _cfgs, ci = classify_collected_files(configs)
        assert ".gitlab-ci.yml" in ci

    def test_makefile_classified_as_ci(self) -> None:
        configs = {"Makefile": "all: test"}
        _deps, _cfgs, ci = classify_collected_files(configs)
        assert "Makefile" in ci

    def test_unrecognized_file_excluded(self) -> None:
        configs = {"README.md": "# My Project"}
        deps, cfgs, ci = classify_collected_files(configs)
        assert not deps
        assert not cfgs
        assert not ci

    def test_empty_input(self) -> None:
        deps, cfgs, ci = classify_collected_files({})
        assert not deps
        assert not cfgs
        assert not ci

    def test_go_mod_is_dependency(self) -> None:
        configs = {"go.mod": "module example.com/app"}
        deps, _cfgs, _ci = classify_collected_files(configs)
        assert "go.mod" in deps

    def test_cargo_toml_is_dependency(self) -> None:
        configs = {"Cargo.toml": '[package]\nname = "app"'}
        deps, _cfgs, _ci = classify_collected_files(configs)
        assert "Cargo.toml" in deps

    def test_eslintrc_is_config(self) -> None:
        configs = {".eslintrc.json": '{"extends": "airbnb"}'}
        _deps, cfgs, _ci = classify_collected_files(configs)
        assert ".eslintrc.json" in cfgs

    def test_multiple_files_classified(self) -> None:
        configs = {
            "pyproject.toml": "[project]",
            "package.json": "{}",
            ".github/workflows/ci.yml": "name: CI",
            "ruff.toml": "line-length = 100",
        }
        deps, cfgs, ci = classify_collected_files(configs)
        assert len(deps) == 2  # pyproject.toml + package.json
        assert len(cfgs) == 2  # pyproject.toml + ruff.toml
        assert len(ci) == 1


# ── detect_package_managers ───────────────────────────────────────────


class TestDetectPackageManagers:
    """Package manager detection from lock files."""

    def test_uv_from_lock(self) -> None:
        tree = ("src/main.py", "pyproject.toml", "uv.lock")
        assert detect_package_managers(tree) == ("uv",)

    def test_npm_from_lock(self) -> None:
        tree = ("src/index.js", "package.json", "package-lock.json")
        assert detect_package_managers(tree) == ("npm",)

    def test_yarn_from_lock(self) -> None:
        tree = ("src/index.js", "package.json", "yarn.lock")
        assert detect_package_managers(tree) == ("yarn",)

    def test_pnpm_from_lock(self) -> None:
        tree = ("src/index.ts", "package.json", "pnpm-lock.yaml")
        assert detect_package_managers(tree) == ("pnpm",)

    def test_go_modules(self) -> None:
        tree = ("main.go", "go.mod", "go.sum")
        assert detect_package_managers(tree) == ("go modules",)

    def test_cargo(self) -> None:
        tree = ("src/main.rs", "Cargo.toml", "Cargo.lock")
        assert detect_package_managers(tree) == ("cargo",)

    def test_poetry(self) -> None:
        tree = ("pyproject.toml", "poetry.lock")
        assert detect_package_managers(tree) == ("poetry",)

    def test_pipenv(self) -> None:
        tree = ("Pipfile", "Pipfile.lock")
        assert detect_package_managers(tree) == ("pipenv",)

    def test_bundler(self) -> None:
        tree = ("Gemfile", "Gemfile.lock")
        assert detect_package_managers(tree) == ("bundler",)

    def test_pip_fallback(self) -> None:
        """requirements.txt without lock file → pip."""
        tree = ("requirements.txt", "main.py")
        assert detect_package_managers(tree) == ("pip",)

    def test_pip_not_detected_with_lock(self) -> None:
        """If a lock file exists, pip fallback should not trigger."""
        tree = ("requirements.txt", "poetry.lock", "pyproject.toml")
        assert detect_package_managers(tree) == ("poetry",)

    def test_multiple_managers(self) -> None:
        tree = ("uv.lock", "package-lock.json", "pyproject.toml", "package.json")
        result = detect_package_managers(tree)
        assert "npm" in result
        assert "uv" in result

    def test_empty_tree(self) -> None:
        assert detect_package_managers(()) == ()

    def test_no_lock_no_requirements(self) -> None:
        tree = ("main.py", "pyproject.toml")
        assert detect_package_managers(tree) == ()

    def test_result_is_sorted(self) -> None:
        tree = ("yarn.lock", "uv.lock", "Cargo.lock")
        result = detect_package_managers(tree)
        assert result == tuple(sorted(result))


# ── detect_layout ─────────────────────────────────────────────────────


class TestDetectLayout:
    """Layout detection from file tree."""

    def test_src_layout(self) -> None:
        tree = ("src/app/__init__.py", "src/app/main.py", "pyproject.toml")
        assert detect_layout(tree) == "src"

    def test_flat_layout(self) -> None:
        tree = ("main.py", "utils.py", "pyproject.toml")
        assert detect_layout(tree) == "flat"

    def test_monorepo_packages(self) -> None:
        tree = ("packages/api/src/index.ts", "packages/web/src/index.ts")
        assert detect_layout(tree) == "monorepo"

    def test_monorepo_apps_and_src(self) -> None:
        tree = ("apps/web/index.ts", "src/shared/utils.ts")
        assert detect_layout(tree) == "monorepo"

    def test_monorepo_multiple_dep_dirs(self) -> None:
        """Multiple top-level dirs with package files → monorepo."""
        tree = ("frontend/package.json", "backend/pyproject.toml", "shared/lib.py")
        assert detect_layout(tree) == "monorepo"

    def test_apps_only_without_src_not_monorepo(self) -> None:
        """apps/ alone without src/ is not monorepo."""
        tree = ("apps/users/models.py", "manage.py")
        assert detect_layout(tree) == "flat"

    def test_no_layout_detected(self) -> None:
        tree = ("README.md", "LICENSE")
        assert detect_layout(tree) is None

    def test_empty_tree(self) -> None:
        assert detect_layout(()) is None

    def test_go_flat_layout(self) -> None:
        tree = ("main.go", "handler.go", "go.mod")
        assert detect_layout(tree) == "flat"

    def test_rust_src_layout(self) -> None:
        tree = ("src/main.rs", "src/lib.rs", "Cargo.toml")
        assert detect_layout(tree) == "src"

    def test_java_src_layout(self) -> None:
        tree = ("src/main/java/App.java", "pom.xml")
        assert detect_layout(tree) == "src"


# ── check_file_tree_truncation ────────────────────────────────────────


class TestCheckFileTreeTruncation:
    """File tree truncation detection."""

    def test_under_limit(self) -> None:
        tree = [f"file_{i}.py" for i in range(10)]
        assert check_file_tree_truncation(tree) is False

    def test_at_limit(self) -> None:
        tree = [f"file_{i}.py" for i in range(FILE_TREE_LIMIT)]
        assert check_file_tree_truncation(tree) is True

    def test_over_limit(self) -> None:
        tree = [f"file_{i}.py" for i in range(FILE_TREE_LIMIT + 100)]
        assert check_file_tree_truncation(tree) is True

    def test_empty_tree(self) -> None:
        assert check_file_tree_truncation([]) is False

    @pytest.mark.parametrize(
        "count",
        [0, 1, FILE_TREE_LIMIT - 1],
        ids=["empty", "single", "just-under"],
    )
    def test_below_limit_cases(self, count: int) -> None:
        tree = [f"f{i}.py" for i in range(count)]
        assert check_file_tree_truncation(tree) is False


# ── sanitize_secrets ──────────────────────────────────────────────────


class TestSanitizeSecrets:
    """Secret value redaction from file contents."""

    # -- env-style KEY=value / KEY: value --

    def test_api_key_yaml(self) -> None:
        content = "env:\n  API_KEY: sk-abc123def456"
        result = sanitize_secrets(content)
        assert "sk-abc123def456" not in result
        assert "API_KEY" in result
        assert "***" in result

    def test_token_equals(self) -> None:
        content = "GITHUB_TOKEN=ghp_xxxxxxxxxxxx"
        result = sanitize_secrets(content)
        assert "ghp_xxxxxxxxxxxx" not in result
        assert "GITHUB_TOKEN" in result

    def test_secret_with_quotes(self) -> None:
        content = 'MY_SECRET: "super-secret-value"'
        result = sanitize_secrets(content)
        assert "super-secret-value" not in result
        assert "MY_SECRET" in result

    def test_password_yaml_key(self) -> None:
        content = "password: hunter2"
        result = sanitize_secrets(content)
        assert "hunter2" not in result
        assert "password" in result

    def test_auth_token_yaml_key(self) -> None:
        content = "auth_token: tok_123abc"
        result = sanitize_secrets(content)
        assert "tok_123abc" not in result
        assert "auth_token" in result

    # -- Template references preserved --

    def test_github_secrets_ref_preserved(self) -> None:
        content = "API_KEY: ${{ secrets.API_KEY }}"
        result = sanitize_secrets(content)
        assert "${{ secrets.API_KEY }}" in result

    def test_env_var_ref_preserved(self) -> None:
        content = "password: ${DATABASE_PASSWORD}"
        result = sanitize_secrets(content)
        assert "${DATABASE_PASSWORD}" in result

    # -- URL credentials --

    def test_url_with_credentials(self) -> None:
        content = "registry: https://user:s3cret@registry.example.com/v2"
        result = sanitize_secrets(content)
        assert "s3cret" not in result
        assert "user" not in result
        assert "https://***@" in result

    def test_url_without_credentials_unchanged(self) -> None:
        content = "homepage: https://example.com"
        result = sanitize_secrets(content)
        assert content == result

    # -- Non-secret content unchanged --

    def test_normal_yaml_unchanged(self) -> None:
        content = "name: CI\non:\n  push:\n    branches: [main]"
        result = sanitize_secrets(content)
        assert result == content

    def test_tool_commands_unchanged(self) -> None:
        content = "run: ruff check --fix src/\nrun: pytest --cov=80"
        result = sanitize_secrets(content)
        assert result == content

    def test_version_strings_unchanged(self) -> None:
        content = "python-version: '3.13'\nnode-version: 22"
        result = sanitize_secrets(content)
        assert result == content

    def test_empty_string(self) -> None:
        assert sanitize_secrets("") == ""

    # -- Mixed content --

    def test_mixed_secrets_and_normal(self) -> None:
        content = (
            "name: CI\n"
            "env:\n"
            "  DB_PASSWORD: mysecretpass\n"
            "  NODE_ENV: production\n"
            "steps:\n"
            "  - run: pytest\n"
        )
        result = sanitize_secrets(content)
        assert "mysecretpass" not in result
        assert "DB_PASSWORD" in result
        assert "NODE_ENV: production" in result
        assert "pytest" in result

    def test_multiple_secrets_redacted(self) -> None:
        content = "API_KEY: key123\nAPI_SECRET: secret456\ntoken: tok789\n"
        result = sanitize_secrets(content)
        assert "key123" not in result
        assert "secret456" not in result
        assert "tok789" not in result
