# Task 1.2: RepositoryProvider ABC + GitHub/GitLab

| Поле | Значення |
|------|----------|
| **Фаза** | 1 — Abstractions |
| **Оцінка** | 4-5 годин |
| **Залежності** | Немає |
| **Блокує** | 2.3, 2.4, 2.6 |
| **Файли** | `integrations/repository.py`, `github.py`, `gitlab.py` |

---

## Що робимо

Створюємо ABC для доступу до метаданих і файлів репозиторію.
Реалізуємо для GitHub (PyGithub) і GitLab (python-gitlab).
Інтегруємо в існуючі клієнти через multiple inheritance.

## Навіщо

Discovery потребує: мови проєкту, file tree (для пошуку конфігів),
вміст CI-файлів і конфігів. Все це є в Platform API (0 LLM-токенів),
але зараз не використовується.

## Очікуваний результат

- `RepositoryProvider` ABC з 4 методами
- `RepositoryMetadata` model
- `GitHubClient` реалізує `RepositoryProvider`
- `GitLabClient` реалізує `RepositoryProvider`
- Unit-тести для обох

## Як перевірити

```bash
make check
pytest tests/unit/test_repository_provider.py
```

## Особливості

- `GitHubClient(GitProvider, RepositoryProvider)` — один об'єкт, два інтерфейси
- `get_file_tree()` може повертати тисячі файлів — потрібна пагінація/ліміт
- `get_file_content()` повертає `None` для binary файлів
- GitHub `get_languages()` повертає bytes → потрібно конвертувати в %
