# Task 2.4: Remove raw_yaml from CIInsights

## Тип: Security | Пріоритет: MEDIUM | Estimate: 30min

## Для борди

`CIInsights.raw_yaml` зберігає повний контент CI файлу. CI файли іноді містять hardcoded secrets (погана практика, але трапляється). Через Pydantic `repr()` вони можуть потрапити в логи.

**Acceptance Criteria:**
- [ ] `raw_yaml` видалений з `CIInsights` або замінений на `repr=False`
- [ ] Жоден caller не використовує `raw_yaml`
- [ ] Tests оновлені

## Implementation

### Перевірити callers

```bash
grep -rn "raw_yaml" src/
```

Якщо `raw_yaml` не використовується ніде (тільки передається в LLM prompt через `build_interpretation_prompt`) — видалити поле.

Якщо використовується в prompts — замінити на `repr=False`:

```python
class CIInsights(BaseModel):
    raw_yaml: str = Field(default="", description="...", repr=False)
```

### Рекомендація

Поле `raw_yaml` передбачалось для LLM interpretation (Layer 3). Але `build_interpretation_prompt()` вже отримує CI insights structured. `raw_yaml` — redundant.

**Видалити поле повністю.** Якщо в Beta-1 знадобиться raw content для LLM — передавати як окремий parameter, не зберігати в моделі.

## Checklist

- [ ] Перевірити callers `raw_yaml`
- [ ] Видалити або `repr=False`
- [ ] Оновити тести
- [ ] `make check` passes
