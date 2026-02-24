# Task 2.3: Config Collection — Implementation Guide

## SmartConfigSelector

```python
# Маппінг: tool name → можливі конфіг-файли
TOOL_CONFIG_MAP: dict[str, list[str]] = {
    "ruff": ["pyproject.toml", "ruff.toml", ".ruff.toml"],
    "mypy": ["pyproject.toml", "mypy.ini", ".mypy.ini", "setup.cfg"],
    "pytest": ["pyproject.toml", "pytest.ini", "setup.cfg", "conftest.py"],
    "eslint": [".eslintrc.js", ".eslintrc.json", ".eslintrc.yml", "eslint.config.js"],
    "prettier": [".prettierrc", ".prettierrc.json", ".prettierrc.yml"],
    "golangci-lint": [".golangci.yml", ".golangci.yaml"],
    # ...
}

# Маппінг: мова → загальні конфіг-файли
LANGUAGE_CONFIG_MAP: dict[str, list[str]] = {
    "Python": ["pyproject.toml", "setup.cfg", "setup.py", "tox.ini", ".pre-commit-config.yaml"],
    "JavaScript": ["package.json", "tsconfig.json", ".babelrc"],
    "TypeScript": ["package.json", "tsconfig.json"],
    "Go": ["go.mod", "go.sum"],
    "Rust": ["Cargo.toml"],
}


class SmartConfigSelector:

    def select_targeted(self, platform_data, ci_insights) -> list[str]:
        """CI є → тільки конфіги згаданих інструментів."""
        paths = set()
        for tool in ci_insights.detected_tools:
            for config_path in TOOL_CONFIG_MAP.get(tool.name, []):
                if config_path in platform_data.file_tree:
                    paths.add(config_path)
        return sorted(paths)

    def select_broad(self, platform_data) -> list[str]:
        """CI нема → всі відомі конфіги для знайдених мов."""
        paths = set()
        for lang in platform_data.languages:
            for config_path in LANGUAGE_CONFIG_MAP.get(lang, []):
                if config_path in platform_data.file_tree:
                    paths.add(config_path)
        return sorted(paths)
```

## ConfigCollector

```python
class ConfigContent(BaseModel):
    model_config = ConfigDict(frozen=True)
    path: str
    content: str
    size_chars: int
    truncated: bool = False


class ConfigCollector:
    MAX_CHARS_PER_FILE = 10_000
    MAX_CHARS_TOTAL = 50_000

    def __init__(self, repo_provider: RepositoryProvider) -> None:
        self._repo = repo_provider

    def collect(
        self, repo_name: str, paths: list[str],
    ) -> tuple[ConfigContent, ...]:
        results = []
        total_chars = 0

        for path in paths:
            if total_chars >= self.MAX_CHARS_TOTAL:
                break
            content = self._repo.get_file_content(repo_name, path)
            if content is None:
                continue
            truncated = len(content) > self.MAX_CHARS_PER_FILE
            if truncated:
                content = content[:self.MAX_CHARS_PER_FILE]
            results.append(ConfigContent(
                path=path,
                content=content,
                size_chars=len(content),
                truncated=truncated,
            ))
            total_chars += len(content)

        return tuple(results)
```

---

## Чеклист

- [ ] `SmartConfigSelector` — targeted + broad modes
- [ ] `ConfigCollector` — read with limits
- [ ] `TOOL_CONFIG_MAP` — ≥10 tools
- [ ] `LANGUAGE_CONFIG_MAP` — ≥5 languages
- [ ] Тести з mock RepositoryProvider
- [ ] `make check` проходить
