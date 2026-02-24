# Task 2.3: Config Collection

| Поле | Значення |
|------|----------|
| **Фаза** | 2 — Discovery Engine |
| **Оцінка** | 2-3 години |
| **Залежності** | 2.1, 2.2, Фаза 1 (RepositoryProvider) |
| **Блокує** | 2.6 |
| **Файли** | `src/ai_reviewer/discovery/config_collector.py` |

## Що робимо

Вибір і читання конфігураційних файлів проєкту.
Targeted режим (CI є → тільки згадані конфіги) і Broad (CI нема → всі відомі).

## Очікуваний результат

- `SmartConfigSelector` — вибирає що читати
- `ConfigCollector` — читає через RepositoryProvider з лімітами
- Ліміти: 10K chars/file, 50K total
