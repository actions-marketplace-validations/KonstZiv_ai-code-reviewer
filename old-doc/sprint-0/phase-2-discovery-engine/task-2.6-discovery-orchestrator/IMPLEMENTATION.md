# Task 2.6: DiscoveryOrchestrator — Implementation Guide

## Повний flow

```python
class DiscoveryOrchestrator:
    CI_FILE_PATTERNS = [
        ".github/workflows/*.yml",
        ".gitlab-ci.yml",
        "Makefile",
    ]

    def __init__(
        self,
        repo_provider: RepositoryProvider,
        conversation: ConversationProvider,
        llm: LLMProvider,
    ) -> None:
        self._repo = repo_provider
        self._conversation = conversation
        self._llm = llm
        self._ci_analyzer = CIPipelineAnalyzer()
        self._config_selector = SmartConfigSelector()

    def discover(
        self, repo_name: str, mr_id: int | None = None,
    ) -> ProjectProfile:

        # 0. Check .reviewbot.md
        existing_config = self._repo.get_file_content(repo_name, ".reviewbot.md")
        if existing_config:
            return parse_reviewbot_md(existing_config)

        # 1. Check previous answers
        answered_gaps: list = []
        if mr_id:
            try:
                threads = self._conversation.get_bot_threads(repo_name, mr_id)
                answered_gaps = self._extract_answers(threads)
            except Exception:
                logger.debug("Could not fetch previous threads")

        # Layer 0: Platform API
        platform_data = self._collect_platform_data(repo_name)

        # Layer 1: CI Pipeline
        ci_insights = self._analyze_ci(platform_data, repo_name)

        # Layer 2: Config files
        configs = self._collect_configs(platform_data, ci_insights, repo_name)

        # Layer 3: Build profile (deterministic or LLM)
        if self._has_enough_data(platform_data, ci_insights, configs):
            profile = self._build_profile_deterministic(
                platform_data, ci_insights, configs,
            )
        else:
            profile = self._build_profile_with_llm(
                platform_data, ci_insights, configs,
            )

        # Enrich from answered questions
        if answered_gaps:
            profile = self._enrich_from_answers(profile, answered_gaps)

        # Post new questions if gaps remain
        if mr_id and profile.gaps:
            self._post_questions_if_needed(repo_name, mr_id, profile, threads)

        return profile
```

## Ключові методи

### _collect_platform_data()

```python
def _collect_platform_data(self, repo_name: str) -> PlatformData:
    languages = self._repo.get_languages(repo_name)
    metadata = self._repo.get_metadata(repo_name)
    file_tree = self._repo.get_file_tree(repo_name)

    primary = max(languages, key=languages.get) if languages else "Unknown"
    ci_paths = self._find_ci_files(file_tree)

    return PlatformData(
        languages=languages,
        primary_language=primary,
        topics=metadata.topics,
        description=metadata.description,
        license=metadata.license,
        default_branch=metadata.default_branch,
        file_tree=file_tree,
        ci_config_paths=ci_paths,
    )
```

### _analyze_ci()

```python
def _analyze_ci(self, platform_data, repo_name) -> CIInsights | None:
    for ci_path in platform_data.ci_config_paths:
        content = self._repo.get_file_content(repo_name, ci_path)
        if content:
            if ci_path == "Makefile":
                return self._ci_analyzer.analyze_makefile(content)
            return self._ci_analyzer.analyze(content, ci_path)
    return None
```

### _has_enough_data()

```python
def _has_enough_data(self, platform_data, ci_insights, configs) -> bool:
    """CI + configs → deterministic is enough."""
    return (
        ci_insights is not None
        and len(ci_insights.detected_tools) >= 2
    )
```

### _build_profile_deterministic()

Збирає AutomatedChecks з CI tools, ReviewGuidance з categories,
Gaps з відсутніх категорій.

### _build_profile_with_llm()

```python
def _build_profile_with_llm(self, platform_data, ci_insights, configs):
    prompt = build_interpretation_prompt(platform_data, ci_insights, configs)
    response = self._llm.generate(
        prompt,
        system_prompt=DISCOVERY_SYSTEM_PROMPT,
        response_schema=LLMDiscoveryResponse,
    )
    llm_result = response.content
    # Merge LLM result with deterministic data...
```

### _post_questions_if_needed()

```python
def _post_questions_if_needed(self, repo_name, mr_id, profile, previous_threads):
    already_asked = set()
    for t in previous_threads:
        for q in t.questions:
            already_asked.add(q.text)

    new_gaps = [g for g in profile.gaps if g.question and g.question not in already_asked]
    if not new_gaps:
        return

    questions = [
        BotQuestion(
            question_id=f"Q{i+1}",
            text=gap.question,
            default_assumption=gap.default_assumption,
            context=QuestionContext.DISCOVERY,
        )
        for i, gap in enumerate(new_gaps)
    ]

    intro = self._format_discovery_intro(profile)
    self._conversation.post_question_comment(repo_name, mr_id, questions, intro=intro)
```

---

## Тести — 4 сценарії

1. **Повний стек:** CI + configs → 0 LLM, profile deterministic
2. **Без CI:** fallback Makefile → LLM для interpretation
3. **Мінімальний:** тільки мови → LLM + питання
4. **З відповідями:** previous threads answered → profile enriched

---

## Чеклист

- [ ] `discover()` — повний flow з graceful degradation
- [ ] `_collect_platform_data()` — через RepositoryProvider
- [ ] `_analyze_ci()` — через CIPipelineAnalyzer
- [ ] `_collect_configs()` — через ConfigCollector
- [ ] `_has_enough_data()` — рішення LLM чи ні
- [ ] `_post_questions_if_needed()` — через ConversationProvider
- [ ] Error handling: кожен layer може fail → continue
- [ ] 4 тест-сценарії
- [ ] `make check` проходить
