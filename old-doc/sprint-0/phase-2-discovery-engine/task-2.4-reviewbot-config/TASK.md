# Task 2.4: .reviewbot.md Parser/Generator

| Поле | Значення |
|------|----------|
| **Фаза** | 2 — Discovery Engine |
| **Оцінка** | 2-3 години |
| **Залежності** | 2.1 (models) |
| **Блокує** | 2.6 |
| **Файли** | `src/ai_reviewer/discovery/reviewbot_config.py` |

## Що робимо

Parser і generator для `.reviewbot.md` — конфіг-файл який живе в repo root.
Якщо він є — Discovery його читає і пропускає більшість pipeline.
Якщо нема — Discovery може запропонувати згенерований.

## Очікуваний результат

- `parse_reviewbot_md(content) -> ProjectProfile`
- `generate_reviewbot_md(profile) -> str`
- Толерантний парсер (працює з hand-edited файлами)
- Roundtrip test: generate → parse → compare
