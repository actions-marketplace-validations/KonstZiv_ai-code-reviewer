# Task 4.3: Documentation — Implementation Guide

## ⚠️ Revision Note (Phase 3 → Phase 4)

- Use `BOT_NAME` constant (`"AI ReviewBot"` from `core/config.py`) consistently
  in all documentation — do not hardcode the name.
- Discovery comment now supports `language` parameter and Russian disclaimer.
- Silent mode: discovery comment is NOT posted when no gaps (avoid noise).
- MkDocs site has 6 languages (en, uk, de, es, it, sr) — all must be updated.

---

## Checklist

- [x] README.md — Discovery section added after Features
- [x] README.md — `AI_REVIEWER_DISCOVERY_ENABLED` added to config table
- [x] README.md — GitLab Quick Start env vars fixed (`AI_REVIEWER_*` prefix)
- [x] README.md — Cost Estimate updated: "Gemini 3 Flash Preview"
- [x] examples/README.md — all env vars modernized to `AI_REVIEWER_*`
- [x] examples/README.md — default model updated to `gemini-3-flash-preview`
- [x] examples/README.md — `discovery_enabled` added to config table
- [x] examples/.reviewbot.md — created (Python/FastAPI example)
- [x] docs/en/discovery.md — English reference page
- [x] docs/uk/discovery.md — Ukrainian translation
- [x] docs/de/discovery.md — German translation
- [x] docs/es/discovery.md — Spanish translation
- [x] docs/it/discovery.md — Italian translation
- [x] docs/sr/discovery.md — Montenegrin translation
- [x] docs/{all 6 langs}/configuration.md — Discovery section added
- [x] mkdocs.yml — Discovery added to nav + nav_translations for all 6 langs
- [x] IMPLEMENTATION.md — checklist updated
- [x] `mkdocs build --strict` — verified (all 6 languages, 0 warnings)
- [x] `ruff check` + `pytest` — verified (868 passed, 92% coverage)
