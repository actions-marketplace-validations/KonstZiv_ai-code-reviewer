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

### Після Phase 1 (Discovery Engine) → Перед Phase 2

**Фокус**: чи LLM analysis видає корисні три зони?

- Тестовий запуск на fixture repo → перевірити якість зон
- Чи `DiscoveryResult` містить `attention_zones`, `watch_files`, `framework`?
- Чи Pydantic response schema парситься без помилок?
- Чи watch-files mechanism зберігає/читає кеш?
- Чи MR-aware detection правильно визначає мову diff?
- **Рішення для Phase 2:** чи формат зон зручний для побудови system prompt?

### Після Phase 2 (Review Integration) → Перед Phase 3

**Фокус**: чи review prompt реально покращився?

- Порівняти review prompt ДО і ПІСЛЯ для test repo
- "SKIP formatting" — чи LLM дійсно менше коментує style?
- "FOCUS security" — чи є security-related коментарі?
- Discovery comment — чи зрозумілий для користувача?
- **Рішення для Phase 3:** чи housekeeping не зламає нові інтеграції?

### Після Phase 3 (Housekeeping) → Перед Phase 4

**Фокус**: чи видалення deps зламало щось?

- `make check` MUST pass після видалення `all-providers`
- Перевірити Docker build: `docker build -t test .`
- Якщо `raw_yaml` видалено з `CIInsights` → оновити тести
- **Рішення для Phase 4:** чи cleanup вплинув на CLI/verbose features?

### Після Phase 4 (Polish) → Sprint Done

**Фокус**: фінальна верифікація всього спринту.

- [ ] Повний `make check`
- [ ] Manual test: Discovery на реальному repo (GitHub)
- [ ] `ai-review discover` працює (mock або real)
- [ ] Three zones видимі у discovery comment
- [ ] Docs відповідають коду
- [ ] README links не broken
- [ ] SPRINT.md оновлений з фінальними результатами
