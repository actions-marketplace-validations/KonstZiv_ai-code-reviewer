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

from ai_reviewer.discovery.cache import (
    DiscoveryCache,
    DiscoveryCacheStorage,
    InMemoryDiscoveryCache,
)
from ai_reviewer.discovery.config_collector import ConfigContent
from ai_reviewer.discovery.models import (
    AttentionZone,
    AutomatedChecks,
    CIInsights,
    DetectedTool,
    Gap,
    LLMDiscoveryResult,
    PlatformData,
    ProjectProfile,
    RawProjectData,
    ReviewGuidance,
    ToolCategory,
)
from ai_reviewer.discovery.orchestrator import DiscoveryOrchestrator
from ai_reviewer.discovery.prompts import (
    DISCOVERY_SYSTEM_PROMPT,
    format_discovery_prompt,
)
from ai_reviewer.discovery.reviewbot_config import (
    generate_reviewbot_md,
    parse_reviewbot_md,
)

__all__ = [
    "DISCOVERY_SYSTEM_PROMPT",
    "AttentionZone",
    "AutomatedChecks",
    "CIInsights",
    "ConfigContent",
    "DetectedTool",
    "DiscoveryCache",
    "DiscoveryCacheStorage",
    "DiscoveryOrchestrator",
    "Gap",
    "InMemoryDiscoveryCache",
    "LLMDiscoveryResult",
    "PlatformData",
    "ProjectProfile",
    "RawProjectData",
    "ReviewGuidance",
    "ToolCategory",
    "format_discovery_prompt",
    "generate_reviewbot_md",
    "parse_reviewbot_md",
]
