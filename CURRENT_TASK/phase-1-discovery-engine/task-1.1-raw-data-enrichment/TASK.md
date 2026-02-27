# Task 1.1: Raw Data Enrichment

## 🔙 Контекст

`_build_profile_deterministic()` збирає `_collected_configs` але ігнорує їх вміст.
`file_tree` truncation silent. Go modules не детектуються.

Це **підготовчий** task — забезпечуємо якісні вхідні дані для LLM prompt (task 1.2).

## 🎯 Мета

Детерміністичний path (0 LLM tokens) повертає **максимум** корисних даних:
- Dependencies list (parsed, не raw)
- Framework hints з deps (Django в requires → `framework_hints: ["django"]`)
- Layout detection з file tree
- Go modules detection
- File tree truncation flag

## Що робити

### 1. Fix `_build_profile_deterministic()`

Зараз `_collected_configs` має `_` prefix і ігнорується.

**Змінити:**

```python
# Було: configs збираються але не використовуються
self._collected_configs = configs  # underscore = "private, unused"

# Стає: парсимо deps з configs
raw_data = RawProjectData(
    languages=platform_data.languages,
    file_tree=platform_data.file_tree,
    ci_files=ci_file_contents,           # raw CI YAML/content
    dependency_files=self._parse_dependency_files(configs),
    config_files=self._parse_config_files(configs),
)
```

### 2. `RawProjectData` model

```python
class RawProjectData(BaseModel):
    """Deterministic data collected without LLM."""
    languages: dict[str, float]           # {"Python": 95.2, "Shell": 4.8}
    file_tree: list[str]                  # ["src/", "src/auth.py", ...]
    file_tree_truncated: bool = False     # True якщо tree > limit
    ci_files: dict[str, str]             # {".github/workflows/ci.yml": "content..."}
    dependency_files: dict[str, str]     # {"pyproject.toml": "content...", "go.mod": "..."}
    config_files: dict[str, str]         # {"ruff.toml": "...", ".eslintrc": "..."}
    detected_package_managers: list[str]  # ["uv", "pip", "npm", "go modules"]
```

### 3. Layout detection (deterministic)

```python
def _detect_layout(self, file_tree: list[str]) -> str | None:
    has_src = any(p.startswith("src/") for p in file_tree)
    has_multiple_packages = # heuristic for monorepo
    if has_src:
        return "src"
    elif has_multiple_packages:
        return "monorepo"
    else:
        return "flat"
```

### 4. Go modules + file tree truncation

- `go.mod` в file tree → `detected_package_managers += ["go modules"]`
- File tree > 500 entries → `file_tree_truncated = True` + warning в log

## Tests

- [ ] `_parse_dependency_files()` парсить pyproject.toml → deps list
- [ ] `_parse_dependency_files()` парсить package.json → deps list
- [ ] `_parse_dependency_files()` парсить go.mod → module name + deps
- [ ] `_detect_layout()` з `src/` → "src"
- [ ] `_detect_layout()` без src → "flat"
- [ ] File tree > 500 → `file_tree_truncated = True`
- [ ] Fallback: malformed config → skip, log warning

## Definition of Done

- [ ] `RawProjectData` model створена і заповнюється
- [ ] Dependencies парсяться з pyproject.toml, package.json, go.mod
- [ ] Layout визначається з file tree
- [ ] File tree truncation flag працює
- [ ] Тести покривають happy path + malformed input
- [ ] `make check` passes

## Estimate: 1.5-2h
