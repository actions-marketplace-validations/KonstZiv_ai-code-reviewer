"""Discovery orchestrator — 4-layer pipeline for project context.

Coordinates all Discovery components:

- Layer 0: Platform API (languages, file tree, metadata).
- Layer 1: CI Pipeline analysis (tools, versions, services).
- Layer 2: Config file collection (linter rules, conventions).
- Layer 3: LLM interpretation (only when deterministic layers are insufficient).

Each layer degrades gracefully: failures are logged and skipped.
"""

from __future__ import annotations

import fnmatch
import logging
from typing import TYPE_CHECKING

from ai_reviewer.discovery.ci_analyzer import CIPipelineAnalyzer
from ai_reviewer.discovery.config_collector import (
    ConfigCollector,
    SmartConfigSelector,
)
from ai_reviewer.discovery.models import (
    AttentionZone,  # noqa: TC001
    AutomatedChecks,
    CIInsights,
    Gap,
    LLMDiscoveryResult,
    PlatformData,
    ProjectProfile,
    RawProjectData,
    ReviewGuidance,
    ToolCategory,
)
from ai_reviewer.discovery.parsers import (
    check_file_tree_truncation,
    classify_collected_files,
    detect_layout,
    detect_package_managers,
    sanitize_secrets,
)
from ai_reviewer.discovery.prompts import (
    DISCOVERY_SYSTEM_PROMPT,
    format_discovery_prompt,
)
from ai_reviewer.discovery.reviewbot_config import parse_reviewbot_md
from ai_reviewer.integrations.conversation import (  # noqa: TC001
    BotQuestion,
    BotThread,
    QuestionContext,
    ThreadStatus,
)

if TYPE_CHECKING:
    from ai_reviewer.discovery.config_collector import ConfigContent
    from ai_reviewer.discovery.models import DetectedTool
    from ai_reviewer.integrations.conversation import ConversationProvider
    from ai_reviewer.integrations.repository import RepositoryProvider
    from ai_reviewer.llm.base import LLMProvider

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────

CI_FILE_PATTERNS: tuple[str, ...] = (
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    ".gitlab-ci.yml",
    "Makefile",
)

_MIN_TOOLS_FOR_DETERMINISTIC = 2
_REVIEWBOT_MD_PATH = ".reviewbot.md"


# ── Orchestrator ─────────────────────────────────────────────────────


class DiscoveryOrchestrator:
    """Main Discovery class — ties all layers into a single pipeline.

    Args:
        repo_provider: Access to repository files and metadata.
        conversation: Bot conversation capabilities.
        llm: LLM provider for interpretation when needed.
    """

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

    # ── Public API ───────────────────────────────────────────────

    def discover(
        self,
        repo_name: str,
        mr_id: int | None = None,
    ) -> ProjectProfile:
        """Run the full Discovery pipeline.

        Args:
            repo_name: Repository identifier (e.g. ``owner/repo``).
            mr_id: Merge/pull request number (enables conversation).

        Returns:
            Populated ``ProjectProfile`` for the review prompt.
        """
        # 0. Check .reviewbot.md — skip pipeline if present
        existing = self._repo.get_file_content(repo_name, _REVIEWBOT_MD_PATH)
        if existing:
            logger.info("Found %s, skipping discovery pipeline", _REVIEWBOT_MD_PATH)
            return parse_reviewbot_md(existing)

        # 1. Check previous answers
        threads: tuple[BotThread, ...] = ()
        if mr_id:
            threads = self._fetch_threads(repo_name, mr_id)

        # Layer 0: Platform API
        platform_data = self._collect_platform_data(repo_name)

        # Layer 1: CI Pipeline
        ci_insights = self._analyze_ci(platform_data, repo_name)

        # Layer 2: Config files
        configs = self._collect_configs(platform_data, ci_insights, repo_name)

        # Collect raw data (deterministic, 0 LLM tokens)
        raw_data = _collect_raw_data(platform_data, ci_insights, configs)

        # Layer 3: Build profile
        if _has_enough_data(ci_insights):
            assert ci_insights is not None  # narrowed by _has_enough_data
            profile = _build_profile_deterministic(platform_data, ci_insights, raw_data)
        else:
            profile = self._build_profile_with_llm(platform_data, ci_insights, raw_data)

        # Enrich from answered threads
        profile = _enrich_from_threads(profile, threads)

        # Post new questions if gaps remain
        if mr_id and profile.gaps:
            self._post_questions_if_needed(repo_name, mr_id, profile, threads)

        return profile

    # ── Layer 0: Platform data ───────────────────────────────────

    def _collect_platform_data(self, repo_name: str) -> PlatformData:
        """Collect repository metadata via Platform API."""
        languages = self._repo.get_languages(repo_name)
        metadata = self._repo.get_metadata(repo_name)
        file_tree = self._repo.get_file_tree(repo_name)
        logger.info("Platform data: %d files in tree", len(file_tree))

        primary = max(languages, key=lambda k: languages[k]) if languages else "Unknown"
        ci_paths = _find_ci_files(file_tree)
        logger.info("CI files found: %s", ci_paths if ci_paths else "(none)")

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

    # ── Layer 1: CI analysis ─────────────────────────────────────

    def _analyze_ci(self, platform_data: PlatformData, repo_name: str) -> CIInsights | None:
        """Analyze all CI configuration files and merge results."""
        results: list[CIInsights] = []
        for ci_path in platform_data.ci_config_paths:
            content = self._repo.get_file_content(repo_name, ci_path)
            if not content:
                logger.info("CI file %s: no content returned", ci_path)
                continue
            logger.info("CI file %s: %d chars fetched", ci_path, len(content))
            try:
                if ci_path == "Makefile":
                    result = self._ci_analyzer.analyze_makefile(content)
                else:
                    result = self._ci_analyzer.analyze(content, ci_path)
            except Exception:
                logger.warning("Failed to analyze CI file %s", ci_path, exc_info=True)
            else:
                logger.info(
                    "CI analysis of %s: %d tool(s) detected",
                    ci_path,
                    len(result.detected_tools),
                )
                results.append(result)
        if not results:
            return None
        return _merge_ci_insights(results)

    # ── Layer 2: Config collection ───────────────────────────────

    def _collect_configs(
        self,
        platform_data: PlatformData,
        ci_insights: CIInsights | None,
        repo_name: str,
    ) -> tuple[ConfigContent, ...]:
        """Select and fetch configuration files."""
        if ci_insights and ci_insights.detected_tools:
            paths = self._config_selector.select_targeted(platform_data, ci_insights)
        else:
            paths = self._config_selector.select_broad(platform_data)

        if not paths:
            return ()

        collector = ConfigCollector(self._repo)
        return collector.collect(repo_name, paths)

    # ── Layer 3: LLM interpretation ──────────────────────────────

    def _build_profile_with_llm(
        self,
        platform_data: PlatformData,
        ci_insights: CIInsights | None,
        raw_data: RawProjectData,
    ) -> ProjectProfile:
        """Build profile using LLM when deterministic data is insufficient."""
        prompt = format_discovery_prompt(raw_data)
        try:
            response = self._llm.generate(
                prompt,
                system_prompt=DISCOVERY_SYSTEM_PROMPT,
                response_schema=LLMDiscoveryResult,
            )
            llm_result = response.content
            if not isinstance(llm_result, LLMDiscoveryResult):
                logger.warning("LLM returned unexpected type: %s", type(llm_result))
                return _build_fallback_profile(platform_data, ci_insights)
            if llm_result.gaps:
                for gap in llm_result.gaps:
                    logger.info("LLM discovery gap: %s", gap.observation)
            return _merge_llm_result(platform_data, ci_insights, llm_result)
        except Exception:
            logger.warning("LLM interpretation failed, using fallback", exc_info=True)
            return _build_fallback_profile(platform_data, ci_insights)

    # ── Conversation ─────────────────────────────────────────────

    def _fetch_threads(self, repo_name: str, mr_id: int) -> tuple[BotThread, ...]:
        """Fetch previous bot threads, gracefully."""
        try:
            return self._conversation.get_bot_threads(repo_name, mr_id)
        except Exception:
            logger.debug("Could not fetch previous threads", exc_info=True)
            return ()

    def _post_questions_if_needed(
        self,
        repo_name: str,
        mr_id: int,
        profile: ProjectProfile,
        threads: tuple[BotThread, ...],
    ) -> None:
        """Post questions for unresolved gaps, skipping already-asked ones."""
        already_asked: set[str] = set()
        for thread in threads:
            for q in thread.questions:
                already_asked.add(q.text)

        new_gaps = [g for g in profile.gaps if g.question and g.question not in already_asked]
        if not new_gaps:
            return

        questions: list[BotQuestion] = []
        for i, gap in enumerate(new_gaps):
            if text := gap.question:
                questions.append(
                    BotQuestion(
                        question_id=f"Q{i + 1}",
                        text=text,
                        default_assumption=gap.default_assumption,
                        context=QuestionContext.DISCOVERY,
                    )
                )

        intro = _format_discovery_intro(profile)
        try:
            self._conversation.post_question_comment(repo_name, mr_id, questions, intro=intro)
        except Exception:
            logger.warning("Failed to post discovery questions", exc_info=True)


# ── Pure functions ───────────────────────────────────────────────────


def _find_ci_files(file_tree: tuple[str, ...]) -> tuple[str, ...]:
    """Match CI file patterns against the file tree."""
    matched: list[str] = []
    for path in file_tree:
        for pattern in CI_FILE_PATTERNS:
            if fnmatch.fnmatch(path, pattern):
                matched.append(path)
                break
    return tuple(matched)


def _first_non_none(*values: str | int | None) -> str | int | None:
    """Return the first non-None value, or None."""
    for v in values:
        if v is not None:
            return v
    return None


def _merge_ci_insights(results: list[CIInsights]) -> CIInsights:
    """Merge CIInsights from multiple CI files into a single result.

    Tools are deduplicated by name.  Scalar fields (python_version,
    package_manager, etc.) take the first non-None value encountered.
    The ``ci_file_path`` is set to the file that contributed the most tools.
    """
    seen_tool_names: set[str] = set()
    merged_tools: list[DetectedTool] = []
    merged_services: list[str] = []
    merged_targets: list[str] = []
    best_path = results[0].ci_file_path
    best_tool_count = 0

    for r in results:
        for tool in r.detected_tools:
            if tool.name not in seen_tool_names:
                seen_tool_names.add(tool.name)
                merged_tools.append(tool)
        for svc in r.services:
            if svc not in merged_services:
                merged_services.append(svc)
        for tgt in r.deployment_targets:
            if tgt not in merged_targets:
                merged_targets.append(tgt)
        if len(r.detected_tools) > best_tool_count:
            best_tool_count = len(r.detected_tools)
            best_path = r.ci_file_path

    return CIInsights(
        ci_file_path=best_path,
        detected_tools=tuple(merged_tools),
        services=tuple(merged_services),
        deployment_targets=tuple(merged_targets),
        python_version=_first_non_none(*(r.python_version for r in results)),  # type: ignore[arg-type]
        node_version=_first_non_none(*(r.node_version for r in results)),  # type: ignore[arg-type]
        go_version=_first_non_none(*(r.go_version for r in results)),  # type: ignore[arg-type]
        package_manager=_first_non_none(*(r.package_manager for r in results)),  # type: ignore[arg-type]
        min_coverage=_first_non_none(*(r.min_coverage for r in results)),  # type: ignore[arg-type]
    )


def _has_enough_data(ci_insights: CIInsights | None) -> bool:
    """Decide whether deterministic data is sufficient (no LLM needed)."""
    return (
        ci_insights is not None and len(ci_insights.detected_tools) >= _MIN_TOOLS_FOR_DETERMINISTIC
    )


def _collect_raw_data(
    platform_data: PlatformData,
    ci_insights: CIInsights | None,
    configs: tuple[ConfigContent, ...],
) -> RawProjectData:
    """Collect all deterministic data (0 LLM tokens).

    Classifies collected configs into dependency, config, and CI files.
    CI file contents come from collected configs (variant b — no
    ``CIInsights.raw_files`` needed).
    """
    config_dict = {cfg.path: cfg.content for cfg in configs}
    dep_files, cfg_files, ci_files = classify_collected_files(config_dict)

    # Also include raw_yaml from CI insights if available and not already present
    if ci_insights and ci_insights.raw_yaml and ci_insights.ci_file_path:
        ci_files.setdefault(ci_insights.ci_file_path, ci_insights.raw_yaml)

    # Sanitize all file contents to prevent secret leakage to LLM / logs
    ci_files = {p: sanitize_secrets(c) for p, c in ci_files.items()}
    dep_files = {p: sanitize_secrets(c) for p, c in dep_files.items()}
    cfg_files = {p: sanitize_secrets(c) for p, c in cfg_files.items()}

    return RawProjectData(
        languages=dict(platform_data.languages),
        file_tree=platform_data.file_tree,
        file_tree_truncated=check_file_tree_truncation(platform_data.file_tree),
        ci_files=ci_files,
        dependency_files=dep_files,
        config_files=cfg_files,
        detected_package_managers=detect_package_managers(platform_data.file_tree),
        layout=detect_layout(platform_data.file_tree),
        reviewbot_config=config_dict.get(".reviewbot.md"),
    )


def _build_profile_deterministic(
    platform_data: PlatformData,
    ci_insights: CIInsights,
    raw_data: RawProjectData,
) -> ProjectProfile:
    """Build a ProjectProfile from deterministic data only."""
    ac = _build_automated_checks(ci_insights)
    guidance = _build_review_guidance(ci_insights)
    gaps = _detect_gaps(ci_insights)

    return ProjectProfile(
        platform_data=platform_data,
        ci_insights=ci_insights,
        language_version=ci_insights.python_version
        or ci_insights.node_version
        or ci_insights.go_version,
        package_manager=ci_insights.package_manager,
        layout=raw_data.layout,
        automated_checks=ac,
        guidance=guidance,
        gaps=gaps,
    )


def _build_automated_checks(ci_insights: CIInsights) -> AutomatedChecks:
    """Map detected tools to AutomatedChecks by category."""
    linting: list[str] = []
    formatting: list[str] = []
    type_checking: list[str] = []
    testing: list[str] = []
    security: list[str] = []

    for tool in ci_insights.detected_tools:
        match tool.category:
            case ToolCategory.LINTING:
                linting.append(tool.name)
            case ToolCategory.FORMATTING:
                formatting.append(tool.name)
            case ToolCategory.TYPE_CHECKING:
                type_checking.append(tool.name)
            case ToolCategory.TESTING:
                testing.append(tool.name)
            case ToolCategory.SECURITY:
                security.append(tool.name)

    return AutomatedChecks(
        linting=tuple(linting),
        formatting=tuple(formatting),
        type_checking=tuple(type_checking),
        testing=tuple(testing),
        security=tuple(security),
        ci_provider=_infer_ci_provider(ci_insights.ci_file_path),
    )


def _infer_ci_provider(ci_file_path: str) -> str | None:
    """Infer CI provider name from the config file path."""
    if ".github" in ci_file_path:
        return "GitHub Actions"
    if "gitlab" in ci_file_path.lower():
        return "GitLab CI"
    if ci_file_path == "Makefile":
        return "Makefile"
    return None


def _build_review_guidance(ci_insights: CIInsights) -> ReviewGuidance:
    """Generate review guidance from CI tool categories."""
    skip: list[str] = []
    focus: list[str] = []

    categories = {t.category for t in ci_insights.detected_tools}

    if ToolCategory.LINTING in categories:
        skip.append("Code style and lint issues (handled by CI)")
    if ToolCategory.FORMATTING in categories:
        skip.append("Code formatting (handled by CI)")
    if ToolCategory.TYPE_CHECKING in categories:
        skip.append("Basic type errors (handled by CI)")

    if ToolCategory.SECURITY not in categories:
        focus.append("Security vulnerabilities (no SAST in CI)")
    if ToolCategory.TESTING not in categories:
        focus.append("Test coverage (no test framework in CI)")

    return ReviewGuidance(
        skip_in_review=tuple(skip),
        focus_in_review=tuple(focus),
    )


def _detect_gaps(ci_insights: CIInsights) -> tuple[Gap, ...]:
    """Detect knowledge gaps from missing CI categories."""
    gaps: list[Gap] = []
    categories = {t.category for t in ci_insights.detected_tools}

    if ToolCategory.TESTING not in categories:
        gaps.append(
            Gap(
                observation="No test framework detected in CI",
                question="What test framework does this project use?",
                default_assumption="No automated tests",
            )
        )

    if ToolCategory.SECURITY not in categories:
        gaps.append(
            Gap(
                observation="No security scanner detected in CI",
                default_assumption="No automated security scanning",
            )
        )

    return tuple(gaps)


def _build_fallback_profile(
    platform_data: PlatformData,
    ci_insights: CIInsights | None,
) -> ProjectProfile:
    """Build a minimal profile when LLM interpretation fails."""
    ac = _build_automated_checks(ci_insights) if ci_insights else AutomatedChecks()
    layout = detect_layout(platform_data.file_tree)

    return ProjectProfile(
        platform_data=platform_data,
        ci_insights=ci_insights,
        layout=layout,
        automated_checks=ac,
    )


def _merge_llm_result(
    platform_data: PlatformData,
    ci_insights: CIInsights | None,
    llm_result: LLMDiscoveryResult,
) -> ProjectProfile:
    """Merge LLM interpretation with deterministic data.

    Builds ``AutomatedChecks`` from both CI analysis (if available) and
    LLM attention zones.  Review guidance is derived from attention zones:
    well-covered areas go to ``skip``, not/weakly covered go to ``focus``.
    """
    ac = _build_automated_checks_from_llm(ci_insights, llm_result)
    guidance = _build_guidance_from_zones(llm_result.attention_zones)

    # Merge LLM conventions into guidance
    if llm_result.conventions_detected:
        guidance = ReviewGuidance(
            skip_in_review=guidance.skip_in_review,
            focus_in_review=guidance.focus_in_review,
            conventions=llm_result.conventions_detected,
        )

    return ProjectProfile(
        platform_data=platform_data,
        ci_insights=ci_insights,
        framework=llm_result.framework,
        automated_checks=ac,
        guidance=guidance,
        gaps=tuple(llm_result.gaps),
        attention_zones=llm_result.attention_zones,
    )


def _build_automated_checks_from_llm(
    ci_insights: CIInsights | None,
    llm_result: LLMDiscoveryResult,
) -> AutomatedChecks:
    """Build AutomatedChecks by combining CI analysis with LLM zones.

    CI-detected tools form the base; LLM zones fill in any gaps
    (categories that CI analysis missed).
    """
    base = _build_automated_checks(ci_insights) if ci_insights else AutomatedChecks()

    # Collect LLM-detected tools by category
    linting: list[str] = []
    formatting: list[str] = []
    type_checking: list[str] = []
    testing: list[str] = []
    security: list[str] = []

    area_to_bucket = {
        "linting": linting,
        "lint": linting,
        "static analysis": linting,
        "formatting": formatting,
        "format": formatting,
        "type checking": type_checking,
        "type_checking": type_checking,
        "typing": type_checking,
        "testing": testing,
        "tests": testing,
        "security": security,
        "security scanning": security,
        "sast": security,
    }

    for zone in llm_result.attention_zones:
        bucket = area_to_bucket.get(zone.area.lower())
        if bucket is not None and zone.status == "well_covered":
            bucket.extend(zone.tools)

    # Merge: CI base + LLM fills gaps (dedup via set)
    return AutomatedChecks(
        linting=tuple(dict.fromkeys(base.linting + tuple(linting))),
        formatting=tuple(dict.fromkeys(base.formatting + tuple(formatting))),
        type_checking=tuple(dict.fromkeys(base.type_checking + tuple(type_checking))),
        testing=tuple(dict.fromkeys(base.testing + tuple(testing))),
        security=tuple(dict.fromkeys(base.security + tuple(security))),
    )


def _build_guidance_from_zones(
    zones: tuple[AttentionZone, ...],
) -> ReviewGuidance:
    """Derive review guidance from LLM attention zones."""
    skip: list[str] = []
    focus: list[str] = []

    for zone in zones:
        tools_str = f" ({', '.join(zone.tools)})" if zone.tools else ""
        if zone.status == "well_covered":
            skip.append(f"{zone.area}{tools_str}")
        elif zone.status == "not_covered":
            focus.append(f"{zone.area}{tools_str} — not automated")
        elif zone.status == "weakly_covered":
            focus.append(f"{zone.area}{tools_str} — weak coverage")

    return ReviewGuidance(
        skip_in_review=tuple(skip),
        focus_in_review=tuple(focus),
    )


def _enrich_from_threads(
    profile: ProjectProfile,
    threads: tuple[BotThread, ...],
) -> ProjectProfile:
    """Remove gaps that have been answered in conversation threads."""
    if not threads or not profile.gaps:
        return profile

    answered_questions: set[str] = set()
    for thread in threads:
        if thread.status == ThreadStatus.ANSWERED:
            for q in thread.questions:
                answered_questions.add(q.text)

    remaining_gaps = tuple(g for g in profile.gaps if g.question not in answered_questions)
    if len(remaining_gaps) == len(profile.gaps):
        return profile

    # Rebuild with fewer gaps (frozen model requires reconstruction)
    return profile.model_copy(update={"gaps": remaining_gaps})


def _format_discovery_intro(profile: ProjectProfile) -> str:
    """Format an introductory message for discovery questions."""
    lang = profile.platform_data.primary_language
    tool_count = 0
    if profile.ci_insights:
        tool_count = len(profile.ci_insights.detected_tools)
    return (
        f"I analyzed this **{lang}** project and found **{tool_count}** CI tool(s). "
        "I have a few questions to improve my review:"
    )


__all__ = [
    "CI_FILE_PATTERNS",
    "DiscoveryOrchestrator",
]
