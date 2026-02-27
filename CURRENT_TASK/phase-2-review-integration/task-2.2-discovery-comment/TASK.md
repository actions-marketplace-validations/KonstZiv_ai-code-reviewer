# Task 2.2: Discovery Comment

## 🎯 Мета

Користувач бачить що Discovery дізнався про проєкт.
Два режими:
- **Default:** коментар тільки при gaps (not_covered zones)
- **Verbose:** коментар завжди (`DISCOVERY_VERBOSE=true`)

## Що робити

### 1. Comment Formatter

```python
def format_discovery_comment(
    discovery: DiscoveryResult,
    verbose: bool = False,
) -> str | None:
    """Format discovery results as MR comment.

    Returns None if nothing to report (and not verbose).
    """
    analysis = discovery.llm_analysis
    if not analysis:
        return None

    not_covered = [z for z in analysis.attention_zones if z.status == "not_covered"]
    weak = [z for z in analysis.attention_zones if z.status == "weakly_covered"]

    # Default mode: only if gaps found
    if not verbose and not not_covered and not weak:
        return None

    sections = ["## 🔍 AI ReviewBot — Discovery Report\n"]

    if verbose:
        # Show all zones
        well = [z for z in analysis.attention_zones if z.status == "well_covered"]
        if well:
            items = "\n".join(f"- ✅ **{z.area}** — {z.reason}" for z in well)
            sections.append(f"### Well Covered (skipping in review)\n{items}\n")

    if not_covered:
        items = "\n".join(f"- ❌ **{z.area}** — {z.reason}" for z in not_covered)
        sections.append(f"### Not Covered (focusing in review)\n{items}\n")

    if weak:
        items = "\n".join(
            f"- ⚠️ **{z.area}** — {z.reason}"
            + (f"\n  💡 {z.recommendation}" if z.recommendation else "")
            for z in weak
        )
        sections.append(f"### Could Be Improved\n{items}\n")

    # Stack info
    if analysis.framework:
        sections.append(f"**Stack:** {analysis.stack_summary or analysis.framework}")

    # Cache status
    if discovery.from_cache:
        sections.append("\n---\n*📦 Using cached analysis. "
                       "Will re-analyze when CI config changes.*")

    return "\n".join(sections)
```

### 2. Env var для verbose mode

```python
# settings.py або config
DISCOVERY_VERBOSE = os.getenv("DISCOVERY_VERBOSE", "false").lower() == "true"
```

Action.yml:
```yaml
inputs:
  discovery_verbose:
    description: 'Always post discovery comment (default: only on gaps)'
    required: false
    default: 'false'
```

## Tests

- [ ] Gaps found → comment generated (default mode)
- [ ] No gaps → None (default mode)
- [ ] No gaps + verbose → comment with all zones
- [ ] From cache → cache notice в коментарі
- [ ] Empty analysis → None

## Estimate: 30min-1h
