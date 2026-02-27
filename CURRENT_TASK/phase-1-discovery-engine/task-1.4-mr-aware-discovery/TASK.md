# Task 1.4: MR-Aware Discovery

## 🔙 Контекст

Discovery аналізує РЕПОЗИТОРІЙ. Але review робиться для конкретного MR.
Три edge cases коли repo-level аналіз недостатній:

1. **MR мова ≠ Repo мова** — repo Python, MR = SQL + Dockerfile + YAML
2. **Watch-files в diff** — MR додає bandit до CI. Кеш говорить "security not covered"
3. **Нові deps в MR** — MR додає sqlalchemy. Це і trigger для re-discovery, і security review point

## 🎯 Мета

Discovery **адаптується** до конкретного MR, а не тільки до repo.

## Що робити

### Edge Case 1: Diff Language Analysis

```python
class DiffLanguageProfile(BaseModel):
    """Languages of the actual diff, not the whole repo."""
    languages: dict[str, float]      # {"SQL": 60.0, "YAML": 30.0, "Dockerfile": 10.0}
    primary_language: str             # "SQL"
    matches_repo: bool                # False — repo is Python, diff is SQL
    adaptation_note: str              # "This MR is primarily SQL migrations + CI config"

def analyze_diff_languages(
    diff_files: list[DiffFile],
    repo_languages: dict[str, float],
) -> DiffLanguageProfile:
    """Analyze which languages are actually in this MR's diff."""
    lang_lines: dict[str, int] = {}

    for file in diff_files:
        lang = detect_language_from_extension(file.path)
        lang_lines[lang] = lang_lines.get(lang, 0) + file.added_lines + file.removed_lines

    total = sum(lang_lines.values()) or 1
    languages = {lang: (lines / total) * 100 for lang, lines in lang_lines.items()}

    primary = max(languages, key=languages.get) if languages else "unknown"
    repo_primary = max(repo_languages, key=repo_languages.get) if repo_languages else "unknown"

    return DiffLanguageProfile(
        languages=languages,
        primary_language=primary,
        matches_repo=(primary == repo_primary),
        adaptation_note=_build_adaptation_note(languages, repo_primary),
    )
```

**Вплив на review prompt:**

```
# Якщо diff мова ≠ repo мова, додаємо до system prompt:

⚠️ This MR is primarily SQL (60%) + YAML (30%), not the repo's primary Python.
Adapt your review:
- SQL: Check for injection vulnerabilities, missing indexes, destructive migrations
- YAML: Validate CI configuration, check for exposed secrets
- Don't apply Python-specific conventions to these files
```

### Edge Case 2: Watch-Files in Diff

```python
async def _check_watch_files_in_diff(
    self,
    diff_files: list[DiffFile],
    cached: DiscoveryCache | None,
) -> bool:
    """Check if this MR changes any watch-files.

    If yes → re-run discovery BEFORE review, using SOURCE BRANCH versions.
    """
    if cached is None:
        return False  # No cache → will run anyway

    diff_paths = {f.path for f in diff_files}
    watch_paths = set(cached.watch_files_snapshot.keys())

    overlap = diff_paths & watch_paths

    if overlap:
        logger.info(
            "MR modifies watch-files: %s. Re-running discovery with source branch.",
            overlap,
        )
        return True

    return False
```

**Важливо:** при re-discovery використовувати файли з SOURCE BRANCH (не target).
Тобто якщо MR додає bandit до CI, Discovery має аналізувати CI **з bandit**.

```python
if watch_files_in_diff:
    # Re-collect raw data from SOURCE branch
    raw_data = await self._collect_raw_data(
        platform_data=platform_data,
        ci_insights=None,  # Don't use old CI insights
        collected_configs=await self._fetch_configs_from_branch(
            repo, repo_key, source_branch
        ),
    )
    # Force LLM re-analysis
    result = await self._analyze_with_llm(raw_data, llm)
```

### Edge Case 3: New Dependencies in Diff

```python
class DiffDepsChange(BaseModel):
    """Dependencies changed in this MR."""
    added: list[str] = []        # ["sqlalchemy", "alembic"]
    removed: list[str] = []      # ["django-extensions"]
    changed_version: list[str] = []  # ["django: 5.0→5.1"]

def detect_deps_changes(
    diff_files: list[DiffFile],
    dependency_file_names: set[str] = DEPENDENCY_FILES,
) -> DiffDepsChange | None:
    """Detect dependency changes from diff.

    Simple heuristic: if pyproject.toml/package.json/go.mod changed,
    extract added/removed lines that look like dependencies.
    """
    dep_diffs = [f for f in diff_files if PurePath(f.path).name in dependency_file_names]

    if not dep_diffs:
        return None

    added, removed = [], []
    for f in dep_diffs:
        for line in f.added_lines_content:
            dep = _extract_dep_name(line, f.path)
            if dep:
                added.append(dep)
        for line in f.removed_lines_content:
            dep = _extract_dep_name(line, f.path)
            if dep:
                removed.append(dep)

    if not added and not removed:
        return None

    return DiffDepsChange(added=added, removed=removed)
```

**Вплив на review prompt:**

```
## New Dependencies Added
- sqlalchemy (new) — check: license compatibility, known vulnerabilities, necessity
- alembic (new) — typically used with sqlalchemy for migrations

⚠️ New dependencies increase attack surface. Verify they are necessary and from trusted sources.
```

### Інтеграція в orchestrator

```python
async def discover_for_mr(
    self,
    repo_key: str,
    mr_id: int,
    diff_files: list[DiffFile],
    ...
) -> DiscoveryResult:
    """Full discovery flow for a specific MR."""

    # 1. Check cache
    should_rerun, cached = await self._should_rerun_discovery(...)

    # 2. Check if MR itself changes watch-files
    if not should_rerun and cached:
        if await self._check_watch_files_in_diff(diff_files, cached):
            should_rerun = True  # Force re-run with source branch

    # 3. Run or use cache
    if should_rerun:
        raw_data = await self._collect_raw_data(...)
        llm_result = await self._analyze_with_llm(raw_data, self.llm)
    else:
        llm_result = cached.result

    # 4. MR-specific enrichment (always runs, cheap)
    diff_langs = analyze_diff_languages(diff_files, raw_data.languages)
    deps_change = detect_deps_changes(diff_files)

    # 5. Compose final result
    return DiscoveryResult(
        llm_analysis=llm_result,
        diff_languages=diff_langs,
        deps_changes=deps_change,
        from_cache=not should_rerun,
    )
```

## Tests

- [ ] `analyze_diff_languages()` — Python repo + SQL diff → `matches_repo=False`
- [ ] `analyze_diff_languages()` — Python repo + Python diff → `matches_repo=True`
- [ ] Watch-files in diff detected → `should_rerun=True`
- [ ] Watch-files NOT in diff → `should_rerun=False` (use cache)
- [ ] New deps detected from pyproject.toml diff
- [ ] New deps detected from package.json diff
- [ ] No dep file in diff → `None`

## Definition of Done

- [ ] Diff language analysis працює
- [ ] Watch-files-in-diff detection працює
- [ ] New deps detection працює
- [ ] Orchestrator flow включає всі три edge cases
- [ ] Тести
- [ ] `make check` passes

## Estimate: 1.5-2h
