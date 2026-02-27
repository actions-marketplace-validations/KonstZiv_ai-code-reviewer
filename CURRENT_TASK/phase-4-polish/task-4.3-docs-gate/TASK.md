# Task 4.3: Documentation Sync + Final Gate

## 🎯 Мета

Документація відповідає коду після всіх змін спринту.
Фінальна верифікація перед v1.0.0b1 tag.

## Чеклист

### Документація

- [ ] `docs/en/discovery.md` — оновити: три зони замість passive context
- [ ] `docs/en/discovery.md` — додати: watch-files, caching, MR-aware
- [ ] `README.md` — оновити discovery секцію
- [ ] `README.md` — перевірити всі internal links
- [ ] `.reviewbot.md` example — відповідає новому формату
- [ ] `action.yml` — додати `discovery_verbose` input
- [ ] ROADMAP.md — оновити з Beta-0.5 результатами

### API docs

- [ ] `docs/en/api.md` — нові моделі: `RawProjectData`, `LLMDiscoveryResult`, `AttentionZone`
- [ ] Deprecated моделі позначені

### Фінальна верифікація

- [ ] `make check` passes (lint + test + type check)
- [ ] Manual test: Discovery на реальному repo
- [ ] `ai-review discover` CLI працює
- [ ] `DISCOVERY_VERBOSE=true` → comment поститься
- [ ] Docker build succeeds
- [ ] No broken links в docs
- [ ] SPRINT.md оновлений з фінальними результатами

### Після спринту

- [ ] Git tag: `v1.0.0b1`
- [ ] Оновити `sprint-beta-0-after-review.md` — закрити виправлені пункти
- [ ] Створити `sprint-beta-0.5-review.md` — що зроблено, що ні, що далі

## Estimate: 30min
