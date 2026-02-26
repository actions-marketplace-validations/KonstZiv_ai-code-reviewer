# Review Gate: між фазами

## Навіщо

Обов'язкова перевірка між фазами Sprint Beta-0.5.
Після кожної фази — зупинись, перевір, скоригуй наступну фазу.

---

## Чеклист після кожної фази

### 1. Оцінка виконаного

- [ ] Всі tasks фази завершені або свідомо відкладені
- [ ] `make check` passes (lint + test)
- [ ] Нові тести написані для нового коду
- [ ] Немає TODO/FIXME без номера issue

### 2. Аналіз відхилень

- [ ] Чи щось реалізовано інакше ніж заплановано? Записати ЩО і ЧОМУ
- [ ] Чи змінились інтерфейси/моделі? Якщо так → перевірити downstream tasks
- [ ] Чи з'явились нові insights під час роботи?

### 3. Вплив на подальші фази

- [ ] Перечитати EPIC.md наступної фази — чи всі assumptions актуальні?
- [ ] Чи потрібно оновити IMPLEMENTATION.md наступних tasks?
- [ ] Чи з'явились нові tasks які треба додати?

### 4. Корекція документації

- [ ] Оновити SPRINT.md — відмітити виконану фазу
- [ ] Оновити EPIC.md поточної фази — записати фактичні результати
- [ ] Якщо змінились моделі — оновити docs/en/api.md і docs/en/discovery.md

---

## Порядок review gates

### Після Phase 1 (Discovery Quality) → Перед Phase 2

**Фокус**: чи config enrichment змінив моделі?

- Якщо `ProjectProfile` отримав нові поля → оновити `to_prompt_context()`
- Якщо `CIInsights` змінився (Go modules) → оновити fixture expected_profile.json
- Перевірити: чи `_build_profile_deterministic()` тепер заповнює framework/layout/conventions?
- **Рішення для Phase 2:** чи потрібно оновити `.reviewbot.md` generator щоб включити нові дані?

### Після Phase 2 (Housekeeping) → Перед Phase 3

**Фокус**: чи видалення deps зламало щось?

- `make check` MUST pass після видалення `all-providers`
- Перевірити Docker build: `docker build -t test .`
- Якщо `raw_yaml` видалено з `CIInsights` → оновити тести що його використовували
- **Рішення для Phase 3:** чи з'явились нові edge cases після cleanup?

### Після Phase 3 (Reliability) → Перед Phase 4

**Фокус**: чи conftest.py покриває потреби Phase 4?

- Перевірити: чи shared fixtures достатні для тестування CLI command?
- Чи timeout працює коректно з mock providers?
- Чи `_first_non_none` type fixes не зламали caller sites?
- **Рішення для Phase 4:** чи mock fixtures з conftest.py підходять для `ai-review discover` тестів?

### Після Phase 4 (User Experience) → Sprint Done

**Фокус**: фінальна верифікація всього спринту.

- [ ] Повний `make check`
- [ ] Manual test: Discovery на реальному repo (GitHub)
- [ ] `ai-review discover` працює (mock або real)
- [ ] Docs відповідають коду
- [ ] README links не broken
- [ ] SPRINT.md оновлений з фінальними результатами
- [ ] `sprint-beta-0-after-review.md` оновлений (закриті пункти, нові пункти)
