# GitLab: Esempio Avanzato

Configurazione pronta per produzione con tutte le best practice.

---

## Passo 1: Crea un PAT

`User Settings → Access Tokens → Add new token`

| Campo | Valore |
|-------|--------|
| Nome | `ai-code-reviewer` |
| Scope | `api` |
| Scadenza | Secondo necessita |

---

## Passo 2: Aggiungi Variabili

`Settings → CI/CD → Variables`

| Nome | Valore | Opzioni |
|------|--------|---------|
| `GOOGLE_API_KEY` | Chiave API Gemini | Masked |
| `GITLAB_TOKEN` | PAT dal Passo 1 | Masked |

---

## Passo 3: Aggiungi un Job

`.gitlab-ci.yml`:

```yaml
stages:
  - test
  - review

# ... altri job ...

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1

  script:
    - ai-review

  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

  # Non bloccare MR se la revisione fallisce
  allow_failure: true

  # Protezione timeout
  timeout: 10m

  # Puo essere cancellato con nuovo commit
  interruptible: true

  # Non aspettare altri stage
  needs: []

  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
```

---

## Cosa Include

| Funzionalita | Stato | Descrizione |
|--------------|-------|-------------|
| Discussioni inline | :white_check_mark: | Con token PAT |
| Non bloccante | :white_check_mark: | `allow_failure: true` |
| Timeout | :white_check_mark: | 10 minuti |
| Interrompibile | :white_check_mark: | Cancellato con nuovo commit |
| Esecuzione parallela | :white_check_mark: | `needs: []` |
| Lingua personalizzata | :white_check_mark: | `LANGUAGE: uk` |

---

## Variazioni

### GitLab Self-hosted

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    GITLAB_URL: https://gitlab.mycompany.com
```

### Con Docker Registry Personalizzato

```yaml
ai-review:
  # Se ghcr.io non e accessibile
  image: registry.mycompany.com/devops/ai-code-reviewer:latest
```

### Con Log DEBUG

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LOG_LEVEL: DEBUG
```

### Solo per Branch Specifici

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

## Troubleshooting

### La Review Non Pubblica Commenti

1. Controlla i log del job
2. Controlla che `GITLAB_TOKEN` abbia scope `api`
3. Controlla che la pipeline sia in esecuzione per una MR

### "401 Unauthorized"

Token non valido o scaduto. Crea un nuovo PAT.

### "403 Forbidden"

Il token non ha accesso al progetto. Controlla i permessi.

---

## Esempio Completo .gitlab-ci.yml

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

## Prossimo Passo

:point_right: [Configurazione →](../configuration.md)
