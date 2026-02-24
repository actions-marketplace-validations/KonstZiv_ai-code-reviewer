# Task 2.1: Discovery Models — Implementation Guide

## Створити `src/ai_reviewer/discovery/models.py`

Дотримуватись стилю існуючих моделей в `core/models.py`:
frozen, ConfigDict, Field з description, tuple замість list.

### Повний список моделей

```python
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ToolCategory(str, Enum):
    LINTING = "linting"
    FORMATTING = "formatting"
    TYPE_CHECKING = "type_checking"
    TESTING = "testing"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    META = "meta"


class DetectedTool(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Tool name: ruff, eslint, etc.")
    category: ToolCategory
    command: str = Field(default="", description="Full command from CI")
    config_file: str | None = Field(default=None, description="Related config")


class CIInsights(BaseModel):
    model_config = ConfigDict(frozen=True)

    ci_file_path: str = Field(description="CI config path")
    raw_yaml: str = ""
    detected_tools: tuple[DetectedTool, ...] = ()
    python_version: str | None = None
    node_version: str | None = None
    go_version: str | None = None
    package_manager: str | None = None
    services: tuple[str, ...] = ()
    deployment_targets: tuple[str, ...] = ()
    min_coverage: int | None = None


class PlatformData(BaseModel):
    model_config = ConfigDict(frozen=True)

    languages: dict[str, float] = Field(description="{name: percentage}")
    primary_language: str
    topics: tuple[str, ...] = ()
    description: str | None = None
    license: str | None = None
    default_branch: str = "main"
    file_tree: tuple[str, ...] = ()
    ci_config_paths: tuple[str, ...] = ()


class AutomatedChecks(BaseModel):
    model_config = ConfigDict(frozen=True)

    linting: tuple[str, ...] = ()
    formatting: tuple[str, ...] = ()
    type_checking: tuple[str, ...] = ()
    testing: tuple[str, ...] = ()
    security: tuple[str, ...] = ()
    ci_provider: str | None = None


class Gap(BaseModel):
    model_config = ConfigDict(frozen=True)

    observation: str
    question: str | None = None
    default_assumption: str


class ReviewGuidance(BaseModel):
    model_config = ConfigDict(frozen=True)

    skip_in_review: tuple[str, ...] = ()
    focus_in_review: tuple[str, ...] = ()
    conventions: tuple[str, ...] = ()


class ProjectProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    platform_data: PlatformData
    ci_insights: CIInsights | None = None
    framework: str | None = None
    language_version: str | None = None
    package_manager: str | None = None
    layout: str | None = None       # "src", "flat", "monorepo"

    automated_checks: AutomatedChecks = AutomatedChecks()
    guidance: ReviewGuidance = ReviewGuidance()
    gaps: tuple[Gap, ...] = ()

    def to_prompt_context(self) -> str:
        """~200-400 tokens для review prompt."""
        parts = [f"Project: {self.platform_data.primary_language}"]
        if self.framework:
            parts[0] += f" ({self.framework})"
        if self.language_version:
            parts[0] += f" {self.language_version}"
        if self.package_manager:
            parts[0] += f", pkg: {self.package_manager}"
        if self.layout:
            parts[0] += f", layout: {self.layout}"

        ac = self.automated_checks
        auto_parts = []
        for name, tools in [
            ("lint", ac.linting), ("fmt", ac.formatting),
            ("types", ac.type_checking), ("test", ac.testing),
            ("sec", ac.security),
        ]:
            if tools:
                auto_parts.append(f"{name}: {', '.join(tools)}")
        if auto_parts:
            parts.append(f"Automated: {'; '.join(auto_parts)}")

        g = self.guidance
        if g.skip_in_review:
            parts.append(f"Skip: {'; '.join(g.skip_in_review)}")
        if g.focus_in_review:
            parts.append(f"Focus: {'; '.join(g.focus_in_review)}")
        if g.conventions:
            parts.append(f"Conventions: {'; '.join(g.conventions)}")

        return "\n".join(parts)
```

---

## Тести

- Створення кожної моделі з мінімальними/повними даними
- Frozen: спроба мутації → error
- `to_prompt_context()` — перевірити output для різних комбінацій
- Серіалізація: `model_dump()` / `model_validate()`

---

## Чеклист

- [ ] `discovery/__init__.py` з re-exports
- [ ] `discovery/models.py` — всі моделі
- [ ] `to_prompt_context()` — compact, informative
- [ ] Тести
- [ ] `make check` проходить
