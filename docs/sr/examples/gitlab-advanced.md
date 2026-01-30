# GitLab: Napredni primjer

Konfiguracija spremna za produkciju sa svim najboljim praksama.

---

## Korak 1: Kreirajte PAT

`User Settings → Access Tokens → Add new token`

| Polje | Vrijednost |
|-------|-------|
| Name | `ai-code-reviewer` |
| Scopes | `api` |
| Expiration | Po potrebi |

---

## Korak 2: Dodajte varijable

`Settings → CI/CD → Variables`

| Ime | Vrijednost | Opcije |
|------|-------|---------|
| `GOOGLE_API_KEY` | Gemini API ključ | Masked |
| `GITLAB_TOKEN` | PAT iz Koraka 1 | Masked |

---

## Korak 3: Dodajte job

`.gitlab-ci.yml`:

```yaml
stages:
  - test
  - review

# ... ostali job-ovi ...

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1

  script:
    - ai-review

  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

  # Ne blokiraj MR ako revizija ne uspije
  allow_failure: true

  # Zaštita timeout-om
  timeout: 10m

  # Može se otkazati na novi commit
  interruptible: true

  # Ne čekaj druge faze
  needs: []

  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
```

---

## Šta je uključeno

| Funkcionalnost | Status | Opis |
|---------|--------|-------------|
| Inline diskusije | :white_check_mark: | Sa PAT tokenom |
| Neblokirajući | :white_check_mark: | `allow_failure: true` |
| Timeout | :white_check_mark: | 10 minuta |
| Prekidiv | :white_check_mark: | Otkazuje se na novi commit |
| Paralelno pokretanje | :white_check_mark: | `needs: []` |
| Prilagođeni jezik | :white_check_mark: | `LANGUAGE: uk` |

---

## Varijacije

### Self-hosted GitLab

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    GITLAB_URL: https://gitlab.mycompany.com
```

### Sa prilagođenim Docker registrom

```yaml
ai-review:
  # Ako ghcr.io nije dostupan
  image: registry.mycompany.com/devops/ai-code-reviewer:latest
```

### Sa DEBUG logovima

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LOG_LEVEL: DEBUG
```

### Samo za određene grane

```yaml
ai-review:
  # ...
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: always
    - if: $CI_MERGE_REQUEST_TARGET_BRANCH_NAME == "main"
      when: always
```

---

## Rješavanje problema

### Revizija ne objavljuje komentare

1. Provjerite logove job-a
2. Provjerite da `GITLAB_TOKEN` ima scope `api`
3. Provjerite da se pipeline pokreće za MR

### "401 Unauthorized"

Token je nevažeći ili je istekao. Kreirajte novi PAT.

### "403 Forbidden"

Token nema pristup projektu. Provjerite dozvole.

---

## Puni primjer .gitlab-ci.yml

```yaml
stages:
  - lint
  - test
  - review
  - deploy

lint:
  stage: lint
  image: python:3.13
  script:
    - pip install ruff
    - ruff check .

test:
  stage: test
  image: python:3.13
  script:
    - pip install pytest
    - pytest

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  timeout: 10m
  interruptible: true
  needs: []
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk

deploy:
  stage: deploy
  script:
    - echo "Deploying..."
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## Sljedeći korak

:point_right: [Konfiguracija →](../configuration.md)
