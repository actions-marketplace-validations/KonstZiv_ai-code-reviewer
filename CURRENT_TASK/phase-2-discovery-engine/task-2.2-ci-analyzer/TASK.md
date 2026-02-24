# Task 2.2: CIPipelineAnalyzer

| Поле | Значення |
|------|----------|
| **Фаза** | 2 — Discovery Engine |
| **Оцінка** | 3-4 години |
| **Залежності** | 2.1 (models) |
| **Блокує** | 2.3, 2.6 |
| **Файли** | `src/ai_reviewer/discovery/ci_analyzer.py` |

## Що робимо

Детерміністичний парсер CI-файлів. Regex-патерни для інструментів,
версій, package managers. **0 LLM-токенів.**

## Навіщо

CI pipeline — найбагатше джерело інформації після мов. Якщо проєкт має
`ruff check` і `mypy --strict` в CI — бот не повинен коментувати
форматування і базові type errors.

## Очікуваний результат

- `CIPipelineAnalyzer.analyze(yaml_content, ci_path) -> CIInsights`
- `analyze_makefile(content) -> CIInsights` (fallback)
- Покриття: Python, JS/TS, Go, Rust (основні інструменти)
- Мінімум 5 YAML test fixtures

## Як перевірити

```bash
pytest tests/unit/test_discovery/test_ci_analyzer.py
```
