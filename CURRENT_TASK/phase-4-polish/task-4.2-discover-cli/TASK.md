# Task 4.2: `ai-review discover` CLI

## 🎯 Мета

Standalone команда для тестування Discovery без створення MR.

```bash
$ ai-review discover owner/repo

🔍 Discovering project context...

📋 Project Profile:
  Stack: Python 3.13 (Django 5.1)
  Package manager: uv
  Layout: src

🔧 Attention Zones:
  ✅ formatting — ruff --format enforced in CI
  ✅ type_checking — mypy --strict in CI
  ⚠️ testing — pytest exists but no coverage threshold
     💡 Add --cov-fail-under=80
  ❌ security — no SAST tool found
     💡 Add bandit for Python security scanning

📁 Watch-files (cache triggers):
  .github/workflows/ci.yml
  pyproject.toml
  ruff.toml

💡 Create .reviewbot.md to customize review behavior.
```

## Що робити

### 1. CLI command

```python
# cli.py або __main__.py

import click

@click.group()
def cli():
    """AI Code Reviewer CLI."""

@cli.command()
@click.argument("repo", type=str)  # "owner/repo"
@click.option("--platform", type=click.Choice(["github", "gitlab"]), default="github")
@click.option("--verbose", is_flag=True, help="Show all details")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def discover(repo: str, platform: str, verbose: bool, output_json: bool):
    """Discover project context without creating a review."""
    import asyncio
    result = asyncio.run(_run_discover(repo, platform))

    if output_json:
        click.echo(result.model_dump_json(indent=2))
    else:
        click.echo(format_discovery_cli_output(result, verbose))
```

### 2. CLI output formatter

```python
def format_discovery_cli_output(result: DiscoveryResult, verbose: bool) -> str:
    """Human-friendly CLI output with emoji."""
    lines = ["🔍 Discovery complete\n"]

    analysis = result.llm_analysis
    if not analysis:
        lines.append("⚠️ LLM analysis unavailable. Showing deterministic data only.")
        return "\n".join(lines)

    # Stack
    if analysis.framework:
        lines.append(f"📋 Stack: {analysis.stack_summary or analysis.framework}")

    # Zones
    lines.append("\n🔧 Attention Zones:")
    STATUS_EMOJI = {"well_covered": "✅", "not_covered": "❌", "weakly_covered": "⚠️"}
    for zone in analysis.attention_zones:
        emoji = STATUS_EMOJI.get(zone.status, "•")
        lines.append(f"  {emoji} {zone.area} — {zone.reason}")
        if zone.recommendation:
            lines.append(f"     💡 {zone.recommendation}")

    # Watch-files
    if analysis.watch_files:
        lines.append("\n📁 Watch-files:")
        for f in analysis.watch_files:
            lines.append(f"  {f}")

    # Conventions
    if verbose and analysis.conventions_detected:
        lines.append("\n📝 Conventions:")
        for c in analysis.conventions_detected:
            lines.append(f"  {c}")

    lines.append("\n💡 Create .reviewbot.md to customize review behavior.")
    return "\n".join(lines)
```

### 3. Entry point в pyproject.toml

```toml
[project.scripts]
ai-review = "ai_code_reviewer.cli:cli"
```

## Tests

- [ ] `ai-review discover --help` → показує help
- [ ] `ai-review discover owner/repo --json` → valid JSON
- [ ] `ai-review discover owner/repo` → human-friendly output
- [ ] Invalid repo format → error message

## Estimate: 1-1.5h
