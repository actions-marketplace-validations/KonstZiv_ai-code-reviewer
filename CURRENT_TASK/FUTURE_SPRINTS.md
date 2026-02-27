# Майбутні спринти: Beta-1 → Beta-3

> **Ковзне вікно:** Beta-1 деталізований (ми знаємо фундамент),
> Beta-2 середній рівень, Beta-3 — загальна візія.
>
> Цей документ оновлюється після кожного спринту.
> Останнє оновлення: після планування Beta-0.5.

---

## Sprint Beta-1: Deep Context + Framework Intelligence (20-28h)

### 🔙 Що матимемо після Beta-0.5

- Three attention zones (well / not / weakly covered)
- LLM-driven discovery з watch-files caching
- MR-aware: diff languages, new deps detection
- Dynamic review prompt з SKIP/FOCUS/CHECK інструкціями
- `ai-review discover` CLI
- ConversationProvider ABC (foundation — post questions, read threads)
- Clean codebase ready for v1.0.0b1

### 🎯 Мета Beta-1

**Перетворити zones з класифікації на actionable guidance.**

Beta-0.5 каже: "framework: Django". Beta-1 каже: "Django → перевіряй міграції,
N+1 queries, admin registration, CSRF на custom views".

### Фази (preview)

**Phase 1: Framework-Specific Review Hints (6-8h)**
- Framework registry: Django, FastAPI, Flask, React, Next.js, Vue, Gin, Actix
- Для кожного framework: список типових проблем і що перевіряти
- Integration: framework hints додаються до review prompt

```python
# Приклад:
DJANGO_HINTS = [
    ReviewHint(
        trigger="models.py changed",
        instruction="Check for missing migrations (makemigrations)",
    ),
    ReviewHint(
        trigger="views.py or urls.py changed",
        instruction="Verify CSRF protection on custom POST views",
    ),
    ReviewHint(
        trigger="ORM queries in diff",
        instruction="Check for N+1 query patterns, suggest select_related/prefetch_related",
    ),
]
```

**Phase 2: Test Coverage Gap Detection (4-5h)**
- Edge case 4 з Beta-0.5 планування
- Source file changed → check if corresponding test file in diff
- Heuristic: `src/auth.py` changed, `tests/test_auth.py` NOT in diff → flag
- Не завжди проблема (integration tests) — тому note, не error

**Phase 3: Linked Task Deep Search (4-6h)**
- ConversationProvider enhancement: `get_linked_tasks_deep()`
- GitHub: timeline API, cross-references, closing keywords
- GitLab: related MRs, epic links
- Контекст з linked issues → review знає що MR має робити

**Phase 4: Persistent Cache + Metrics (3-4h)**
- `FileBasedDiscoveryCache` для local dev
- Discovery metrics: tokens used, cache hit rate, zones distribution
- Usage footer в review comment (opt-in)

**Phase 5: Stability (3-4h)**
- Edge cases від реального використання
- Error handling hardening
- Performance profiling
- Documentation для contributors

### Definition of Done (Beta-1)

- [ ] Django/FastAPI/React project → framework-specific review comments
- [ ] Source file changed without test → note in review
- [ ] Linked issues context в review prompt
- [ ] Cache persists між runs (file-based)
- [ ] Usage metrics логуються
- [ ] v1.0.0b2 tag

---

## Sprint Beta-2: Multi-Step Review (15-22h)

### 🔙 Що матимемо після Beta-1

- Framework-specific hints
- Test coverage gap detection
- Deep linked tasks
- Persistent cache
- Mature ConversationProvider

### 🎯 Мета Beta-2

**Review стає multi-step: scout → prioritize → deep review.**

Замість одного LLM-запиту на весь diff:
1. **Scout** — швидкий огляд всіх файлів, класифікація за ризиком
2. **Prioritize** — high-risk файли (auth, security, API) → deep review
3. **Deep review** — детальний аналіз priority файлів з context

### Ключові ідеї

**File Prioritization (edge case 5 з Beta-0.5):**
```
High priority:  auth/*, security/*, api/endpoints/*
Medium:         models/*, services/*, utils/*
Low:            README, configs, migrations (unless destructive)
```

**Scout prompt** (~100 tokens input):
```
Given this diff summary (file list + change sizes),
classify each file by review priority: high/medium/low.
High = security, auth, API. Low = config, docs, auto-generated.
```

**Deep review** — тільки high/medium files, з повним context:
- Related files (imports, callers)
- Framework-specific checks
- Three zones від Discovery

**Token budget:**
```
Beta-0.5: ~500 tokens per MR (one prompt)
Beta-1:   ~800 tokens per MR (with framework hints)
Beta-2:   ~1200-1500 tokens per MR (scout + deep), but BETTER quality
```

### Phases (high-level)

1. Scout engine — file classification
2. Priority-based deep review — different depth per priority
3. Context fetching — related files for high-priority items
4. Integration + fallback (single-pass для small diffs)

### Definition of Done (Beta-2)

- [ ] Large MR (50+ files) → scout identifies top 10 для deep review
- [ ] Auth files → deeper analysis ніж README changes
- [ ] Context fetching працює (imported modules available)
- [ ] Small MR (<5 files) → single-pass (як зараз, не overhead)
- [ ] v1.0.0b3 tag

---

## Sprint Beta-3: Interactive Mode (vision)

### 🔙 Що матимемо після Beta-2

- Multi-step review (scout → deep)
- ConversationProvider з thread participation
- Mature discovery + caching
- Framework intelligence

### 🎯 Мета Beta-3

**Бот стає учасником conversation, а не одноразовим коментатором.**

### Сценарії

**Сценарій 1: Follow-up після review**
```
Bot: "Цей SQL запит може бути вразливий до injection. Рекомендую параметризований запит."
Author: "Це internal tool, тільки адміни мають доступ."
Bot: "Зрозумів, але навіть для internal tools рекомендовано параметризацію.
      Якщо це свідомий вибір — ОК, позначаю як acknowledged."
```

**Сценарій 2: Discovery dialogue**
```
Bot: "Не знайшов CI конфігурацію. Як ви перевіряєте код?
      Якщо не відповісте за 48 годин — припущу що CI відсутній."
Author: "Ми використовуємо Jenkins, конфіг на іншому сервері."
Bot: "Дякую! Оновив профіль проєкту. Які tools в Jenkins? (ruff, pytest, mypy?)"
```

**Сценарій 3: Re-review після fixes**
```
Author: "Виправив SQL injection, прошу re-review."
Bot: [читає thread, бачить що це відповідь на його коментар]
Bot: [перечитує оновлений код]
Bot: "✅ SQL тепер параметризований. Виглядає добре."
```

### Технічні вимоги

- Full thread participation (respond in same thread)
- Question tracking: asked → answered → acknowledged
- Re-review trigger: author requests + bot detects what changed
- State machine: review lifecycle per comment
- Timeout: unanswered questions → use default_assumption

### Phases (high-level)

1. Thread participation — respond in same thread
2. Question lifecycle — track asked/answered/expired
3. Re-review trigger — detect and handle fix requests
4. State machine — review comment lifecycle

### Definition of Done (Beta-3)

- [ ] Bot responds in threads (не top-level comments)
- [ ] Author відповідає на питання → bot updates review
- [ ] "Fixed, please re-review" → bot re-checks specific comments
- [ ] Unanswered questions → default_assumption після timeout
- [ ] v1.0.0rc1 tag

---

## Загальна карта

```
                Beta-0 (done, 85%)          Beta-0.5 (current)
                ─────────────────           ──────────────────
                3 ABCs                      LLM Discovery
                Discovery pipeline          Three attention zones
                ConversationProvider        Watch-files caching
                12K tests                   MR-aware, dynamic prompt

                Beta-1                      Beta-2
                ──────                      ──────
                Framework hints             Scout → Deep review
                Test gap detection          File prioritization
                Deep linked tasks           Context fetching
                Persistent cache            Token optimization

                Beta-3                      v1.0.0 🎉
                ──────                      ────────
                Interactive mode            Production-ready
                Thread dialogue             Full documentation
                Re-review                   PyPI stable release
                Question lifecycle          Docker Hub
```

## Token Budget Across Sprints

| Sprint | Tokens per MR (typical) | Кешовано |
|--------|------------------------|---------|
| Beta-0 | 0 (no LLM in discovery) | — |
| Beta-0.5 | ~500 (discovery) + ~1000 (review) | Watch-files: 0 after first |
| Beta-1 | ~800 + ~1000 | Same + persistent |
| Beta-2 | ~1200-1500 (scout+deep) | Priority = less waste |
| Beta-3 | +~200 per dialogue turn | Incremental |
