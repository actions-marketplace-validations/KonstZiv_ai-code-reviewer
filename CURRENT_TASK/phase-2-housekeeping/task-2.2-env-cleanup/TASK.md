# Task 2.2: Clean .env.example

## Тип: Cleanup | Пріоритет: HIGH | Estimate: 15min

## Для борди

`.env.example` містить `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY` — providers які не підтримуються. Видалити все що не працює.

## Implementation

В `.env.example` залишити ТІЛЬКИ:
```env
# Required: Google Gemini API key
# Get key at: https://aistudio.google.com/
GOOGLE_API_KEY=

# Required (one of): Platform token
# GitHub: https://github.com/settings/tokens
GITHUB_TOKEN=
# GitLab: https://gitlab.com/-/profile/personal_access_tokens
GITLAB_TOKEN=

# Optional settings
AI_REVIEWER_LOG_LEVEL=INFO
AI_REVIEWER_DISCOVERY_ENABLED=true
AI_REVIEWER_REVIEW_LANGUAGE=auto
```

Також перевірити `action.yml` — всі inputs мають відповідати реальним settings.

## Checklist

- [ ] Почистити `.env.example`
- [ ] Перевірити `action.yml` inputs відповідність
- [ ] Оновити docs якщо потрібно
