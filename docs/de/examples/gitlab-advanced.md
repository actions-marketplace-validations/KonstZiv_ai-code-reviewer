# GitLab: Erweitertes Beispiel

Produktionsreife Konfiguration mit allen Best Practices.

---

## Schritt 1: PAT erstellen

`User Settings → Access Tokens → Add new token`

| Feld | Wert |
|------|------|
| Name | `ai-code-reviewer` |
| Scopes | `api` |
| Ablaufdatum | Nach Bedarf |

---

## Schritt 2: Variablen hinzufügen

`Settings → CI/CD → Variables`

| Name | Wert | Optionen |
|------|------|----------|
| `GOOGLE_API_KEY` | Gemini API-Schlüssel | Masked |
| `GITLAB_TOKEN` | PAT aus Schritt 1 | Masked |

---

## Schritt 3: Job hinzufügen

`.gitlab-ci.yml`:

```yaml
stages:
  - test
  - review

# ... andere Jobs ...

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1

  script:
    - ai-review

  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

  # MR nicht blockieren, wenn Review fehlschlägt
  allow_failure: true

  # Timeout-Schutz
  timeout: 10m

  # Kann bei neuem Commit abgebrochen werden
  interruptible: true

  # Nicht auf andere Stages warten
  needs: []

  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
```

---

## Was enthalten ist

| Funktion | Status | Beschreibung |
|----------|--------|--------------|
| Inline-Discussions | :white_check_mark: | Mit PAT-Token |
| Nicht-blockierend | :white_check_mark: | `allow_failure: true` |
| Timeout | :white_check_mark: | 10 Minuten |
| Unterbrechbar | :white_check_mark: | Bei neuem Commit abgebrochen |
| Parallele Ausführung | :white_check_mark: | `needs: []` |
| Benutzerdefinierte Sprache | :white_check_mark: | `LANGUAGE: uk` |

---

## Variationen

### Self-hosted GitLab

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    GITLAB_URL: https://gitlab.mycompany.com
```

### Mit benutzerdefinierter Docker Registry

```yaml
ai-review:
  # Wenn ghcr.io nicht erreichbar ist
  image: registry.mycompany.com/devops/ai-code-reviewer:latest
```

### Mit DEBUG-Logs

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LOG_LEVEL: DEBUG
```

### Nur für bestimmte Branches

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

## Fehlerbehebung

### Review postet keine Kommentare

1. Job-Logs überprüfen
2. Überprüfen, ob `GITLAB_TOKEN` den Scope `api` hat
3. Überprüfen, ob die Pipeline für MR läuft

### "401 Unauthorized"

Token ist ungültig oder abgelaufen. Neuen PAT erstellen.

### "403 Forbidden"

Token hat keinen Zugriff auf das Projekt. Berechtigungen überprüfen.

---

## Vollständiges .gitlab-ci.yml Beispiel

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

## Nächster Schritt

:point_right: [Konfiguration →](../configuration.md)
