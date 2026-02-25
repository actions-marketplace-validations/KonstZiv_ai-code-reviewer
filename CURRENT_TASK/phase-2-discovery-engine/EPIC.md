# Фаза 2: Discovery Engine

## Навігація

```
phase-2-discovery-engine/
├── EPIC.md                            ← ви тут
├── task-2.1-discovery-models/         Pydantic models
├── task-2.2-ci-analyzer/              CI pipeline parser (0 LLM)
├── task-2.3-config-collection/        Smart config reader
├── task-2.4-reviewbot-config/         .reviewbot.md parser/generator
├── task-2.5-discovery-prompts/        LLM prompts for interpretation
└── task-2.6-discovery-orchestrator/   Main orchestrator (connects all)
```

**Батьківський документ:** [../SPRINT.md](../SPRINT.md)

---

## 🔙 Контекст

### Що маємо після Фази 1

- `LLMProvider` ABC — generic generate з будь-якою schema
- `RepositoryProvider` ABC — мови, metadata, file tree, file content
- `ConversationProvider` ABC — питання, відповіді, threads
- Чисті залежності, виправлений N+1

### Що будуємо

4-layer Discovery pipeline як описано в Discovery Phase v3:

```
Layer 0: Platform API → мови, topics, file tree         (0 tokens, 0 cost)
Layer 1: CI Pipeline  → інструменти, версії, coverage   (0 tokens, 0 cost)
Layer 2: Config files → правила, конвенції               (0 tokens, 0 cost)
Layer 3: LLM          → інтерпретація (тільки якщо треба) (мін. tokens)
```

---

## 🎯 Мета фази

Створити всі компоненти Discovery окремо, з тестами.
Кожен модуль самодостатній і тестується ізольовано.

---

## Задачі

| # | Задача | Оцінка | Залежності |
|---|--------|--------|------------|
| 2.1 | Discovery Models | 2-3 год | Фаза 1 (RepositoryMetadata) |
| 2.2 | CIPipelineAnalyzer | 3-4 год | 2.1 |
| 2.3 | Config Collection | 2-3 год | 2.1, Фаза 1 (RepositoryProvider) |
| 2.4 | .reviewbot.md Parser | 2-3 год | 2.1 |
| 2.5 | Discovery Prompts | 2-3 год | 2.1 |
| 2.6 | DiscoveryOrchestrator | 5-7 год | 2.1-2.5, Фаза 1 (всі ABCs) |

---

## Definition of Done

- [ ] `ProjectProfile.to_prompt_context()` генерує compact text
- [ ] CI Analyzer парсить GitHub Actions і GitLab CI YAML
- [ ] Config Collector читає файли з лімітами
- [ ] `.reviewbot.md` roundtrip: generate → parse → equal
- [ ] Orchestrator проходить 4 сценарії (повний стек, без CI, без конфігів, з відповідями)
- [ ] Coverage ≥ 80%

---

## ⚠️ Ревізія після завершення

Перед Фазою 3 перевірити:

1. `ProjectProfile.to_prompt_context()` — чи достатньо інформації для review prompt?
2. Чи формат discovery comment (task 3.3) відповідає реальним даним?
3. Чи orchestrator повертає дані в форматі зручному для `build_review_prompt()`?
4. Чи `ConversationProvider` API виявився зручним під час інтеграції в orchestrator?

---

## 📌 Backlog

### Оптимізація review-контексту для великих PR

**Проблема:** при великих PR промпт перевищує ~38K chars, що провокує
503 UNAVAILABLE та Connection reset від Gemini API. Тестові файли —
найбільша частина контексту, але дають найменшу цінність для review.

**Запропоноване рішення:**
- Виключати тестові файли з review prompt при перевищенні порогу символів
- Пріоритизувати production-код (src/) над тестами (tests/)
- Можливо: окремий lightweight review pass для тестів
- Інтегрувати з Discovery (ProjectProfile знає які файли — тести)

**Scope:** review prompt builder (не Discovery prompts)

---

## 🔭 Як Discovery розвивається далі

| Версія | Зміст |
|--------|-------|
| Beta-0 | Базовий pipeline: Platform → CI → Configs → LLM |
| Beta-1 | Framework-specific knowledge (Django, FastAPI patterns) |
| Beta-2 | Scout agent використовує ProjectProfile для пріоритизації |
| Beta-3 | Auto-update .reviewbot.md при зміні конфігів |
