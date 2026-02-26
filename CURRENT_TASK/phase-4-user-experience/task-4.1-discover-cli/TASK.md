# Task 4.1: `ai-review discover` CLI Command

## Тип: Feature | Пріоритет: HIGH | Estimate: 1-1.5h

## Для борди

Додати підкоманду `ai-review discover` для standalone запуску Discovery pipeline.
Користувач може перевірити що бот дізнався про проєкт без створення MR.

**Acceptance Criteria:**
- [ ] `ai-review discover --repo owner/repo` → виводить ProjectProfile
- [ ] Працює з GitHub і GitLab
- [ ] Rich formatted output (таблиці, кольори, emoji)
- [ ] `--json` flag для machine-readable output
- [ ] Exit code 0 при успіху

---

# Implementation Guide

## Поточний стан CLI

`cli.py` використовує Typer з одним `@app.command()` — `main()`.
Потрібно перетворити на multi-command app або додати subcommand.

### Підхід: Typer callback + додаткова command

```python
# cli.py — додати discover command

@app.command()
def discover(
    repo: Annotated[str, typer.Argument(help="Repository (owner/repo)")],
    provider: Annotated[Provider | None, typer.Option("--provider", "-p")] = None,
    json_output: Annotated[bool, typer.Option("--json", "-j")] = False,
    log_level: Annotated[str, typer.Option("--log-level")] = "WARNING",
) -> None:
    """Run Discovery pipeline on a repository and display results.

    Shows what the bot knows about the project: language, framework,
    CI tools, conventions, and review guidance.

    Examples:
        ai-review discover owner/repo
        ai-review discover owner/repo --json
        ai-review discover owner/repo --provider github
    """
    _setup_logging(log_level)
    settings = get_settings()

    # Auto-detect provider or use specified
    if provider is None:
        provider = _detect_provider_from_settings(settings)

    if provider is None:
        console.print("[red]Error:[/] No provider token found. Set GITHUB_TOKEN or GITLAB_TOKEN.")
        raise typer.Exit(1)

    # Create provider client
    git_client = _create_client(provider, settings)

    # Run discovery
    from ai_reviewer.discovery import DiscoveryOrchestrator
    from ai_reviewer.llm.gemini import GeminiProvider

    llm = GeminiProvider(
        api_key=settings.google_api_key.get_secret_value(),
        model_name=settings.gemini_model,
    )
    orchestrator = DiscoveryOrchestrator(
        repo_provider=git_client,
        conversation=git_client,
        llm=llm,
        timeout_seconds=settings.discovery_timeout,
    )

    console.print("[bold]🔍 Discovering project context...[/]\n")

    try:
        profile = orchestrator.discover(repo, mr_id=None)  # No MR = no conversation
    except Exception as e:
        console.print(f"[red]Discovery failed:[/] {e}")
        raise typer.Exit(1) from e

    if json_output:
        console.print(profile.model_dump_json(indent=2))
    else:
        _print_profile(profile)


def _print_profile(profile: ProjectProfile) -> None:
    """Pretty-print ProjectProfile using Rich."""
    from rich.table import Table

    pd = profile.platform_data

    # Header
    header = f"📋 [bold]Project Profile:[/] {pd.primary_language}"
    if profile.framework:
        header += f" ({profile.framework})"
    if profile.language_version:
        header += f" {profile.language_version}"
    console.print(header)

    if profile.package_manager:
        console.print(f"   Package manager: {profile.package_manager}")
    if profile.layout:
        console.print(f"   Layout: {profile.layout}")

    # CI Tools
    ci = profile.ci_insights
    if ci and ci.detected_tools:
        console.print(f"\n🔧 [bold]CI Tools ({len(ci.detected_tools)}):[/]")
        for tool in ci.detected_tools:
            console.print(f"   ✅ {tool.name} ({tool.category.value})")
    else:
        console.print("\n🔧 [bold]CI Tools:[/] ❌ None detected")

    # Review Guidance
    g = profile.guidance
    if g.skip_in_review or g.focus_in_review:
        console.print("\n📝 [bold]Review Guidance:[/]")
        if g.skip_in_review:
            console.print("   [dim]Skip:[/] " + "; ".join(g.skip_in_review))
        if g.focus_in_review:
            console.print("   [bold]Focus:[/] " + "; ".join(g.focus_in_review))

    if g.conventions:
        console.print("\n📏 [bold]Conventions:[/]")
        for conv in g.conventions:
            console.print(f"   • {conv}")

    # Gaps
    if profile.gaps:
        console.print(f"\n❓ [bold]Gaps ({len(profile.gaps)}):[/]")
        for gap in profile.gaps:
            console.print(f"   • {gap.observation}")
            if gap.question:
                console.print(f"     [dim]Question:[/] {gap.question}")

    console.print("\n💡 [dim]Create .reviewbot.md in repo root to customize.[/]")
```

### Helper functions

```python
def _detect_provider_from_settings(settings: Settings) -> Provider | None:
    """Auto-detect provider from available tokens."""
    if settings.github_token:
        return Provider.GITHUB
    if settings.gitlab_token:
        return Provider.GITLAB
    return None


def _create_client(provider: Provider, settings: Settings):
    """Create appropriate client for the provider."""
    if provider == Provider.GITHUB:
        return GitHubClient(token=settings.github_token.get_secret_value())
    elif provider == Provider.GITLAB:
        return GitLabClient(
            token=settings.gitlab_token.get_secret_value(),
            url=settings.gitlab_url,
        )
```

### Важливо: rename existing `main` command

Typer з двома commands потребує або explicit `app.command(name="review")` або callback pattern.

**Рекомендація:** Залишити `main` як default (без name), додати `discover` як named command.

```python
app = typer.Typer(help="AI Code Reviewer — automated code review for GitHub and GitLab")

@app.command(name="review")  # або без name для backward compat
def main(...): ...

@app.command(name="discover")
def discover(...): ...

# Або: app.callback() для default behavior + named commands
```

**Перевірити backward compatibility:** `ai-review` без subcommand повинен працювати як раніше (review mode).

## Tests

```python
class TestDiscoverCLI:
    def test_discover_json_output(self, mock_settings, sample_platform_data):
        """ai-review discover --json outputs valid JSON."""
        # Test using typer.testing.CliRunner

    def test_discover_no_token(self):
        """ai-review discover without token exits with error."""
```

## Checklist

- [ ] `discover` command в cli.py
- [ ] Rich formatted output
- [ ] `--json` flag
- [ ] Backward compatible (default command still works)
- [ ] Unit test
- [ ] Оновити README з новою командою
- [ ] `make check` passes
