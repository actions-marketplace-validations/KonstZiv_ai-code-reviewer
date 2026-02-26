# Task 2.3: Fix ROADMAP.md

## Тип: Documentation | Пріоритет: MEDIUM | Estimate: 20min

## Для борди

`ROADMAP.md` переміщений в `old-doc/`. README.md і docs посилаються на `ROADMAP.md` в root.

## Implementation

**Два варіанти (вибрати один):**

### Варіант A: Оновити ROADMAP.md і повернути в root

Скопіювати `old-doc/ROADMAP.md` → root, оновити з актуальним станом:
- Beta-0: DONE ✅
- Beta-0.5: IN PROGRESS
- Beta-1: PLANNED
- Beta-2, Beta-3: FUTURE

### Варіант B: Видалити посилання на ROADMAP

Якщо ROADMAP не потрібний — видалити посилання з README.md і docs.

**Рекомендація:** Варіант A. ROADMAP корисний для open-source проєкту — показує що проєкт живий і має план.

Також перемістити `old-doc/PROJECT_STRUCTURE.md` в root якщо він актуальний, або видалити.

## Checklist

- [ ] ROADMAP.md в root, оновлений
- [ ] README links працюють
- [ ] `old-doc/` — вирішити що робити (видалити або залишити як archive)
