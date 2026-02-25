"""Discovery engine for automated project context gathering.

This package implements a 4-layer pipeline that collects project metadata,
CI configuration, tool conventions, and LLM-assisted interpretation to
build a ``ProjectProfile`` used by the review prompt.

Layers:
    0. Platform API — languages, topics, file tree (0 tokens).
    1. CI Pipeline — tools, versions, coverage targets (0 tokens).
    2. Config files — linter rules, conventions (0 tokens).
    3. LLM interpretation — only when deterministic layers are insufficient.
"""

from ai_reviewer.discovery.config_collector import ConfigContent
from ai_reviewer.discovery.models import (
    AutomatedChecks,
    CIInsights,
    DetectedTool,
    Gap,
    PlatformData,
    ProjectProfile,
    ReviewGuidance,
    ToolCategory,
)

__all__ = [
    "AutomatedChecks",
    "CIInsights",
    "ConfigContent",
    "DetectedTool",
    "Gap",
    "PlatformData",
    "ProjectProfile",
    "ReviewGuidance",
    "ToolCategory",
]
