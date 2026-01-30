# Quick Start

Fai funzionare AI Code Reviewer in 1 minuto.

---

## GitHub Actions

### Passo 1: Aggiungi un secret

`Settings → Secrets and variables → Actions → New repository secret`

| Nome | Valore |
|------|--------|
| `GOOGLE_API_KEY` | La tua chiave API Gemini |

:point_right: [Ottieni la tua chiave](https://aistudio.google.com/)

### Passo 2: Crea un workflow

Nella root del tuo progetto, crea il file `.github/workflows/ai-review.yml`

`.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    runs-on: ubuntu-latest
    # Non eseguire per PR da fork (nessun accesso ai secret)
    if: github.event.pull_request.head.repo.full_name == github.repository
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

### Passo 3: Crea un PR

Fatto! La revisione AI apparira automaticamente.

---

## GitLab CI

### Passo 1: Aggiungi una variabile

`Settings → CI/CD → Variables`

| Nome | Valore | Opzioni |
|------|--------|---------|
| `GOOGLE_API_KEY` | La tua chiave API Gemini | Masked, Protected |

:point_right: [Ottieni la tua chiave](https://aistudio.google.com/)

### Passo 2: Aggiungi un job

Nella root del tuo progetto, crea il file `.gitlab-ci.yml`

`.gitlab-ci.yml`:

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  variables:
    GITLAB_TOKEN: $CI_JOB_TOKEN
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

!!! note "Per commenti inline"
    `CI_JOB_TOKEN` ha limitazioni. Per funzionalità completa usa [Personal Access Token](gitlab.md#personal-access-token).

### Passo 3: Crea una MR

Fatto! La revisione AI apparira come commenti sulla MR.

---

## Esecuzione Locale

Per test locali hai bisogno di:

- **GOOGLE_API_KEY** — [ottienila su Google AI Studio](https://aistudio.google.com/)
- **GITHUB_TOKEN** o **GITLAB_TOKEN** — a seconda della piattaforma:
    - GitHub: [come ottenere PAT](github.md#get-token)
    - GitLab: [come ottenere PAT](gitlab.md#get-token)

=== "GitHub"

    ```bash
    # Installa
    pip install ai-reviewbot

    # Configura
    export GOOGLE_API_KEY=your_key
    export GITHUB_TOKEN=your_github_pat

    # Esegui per GitHub PR
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab"

    ```bash
    # Installa
    pip install ai-reviewbot

    # Configura
    export GOOGLE_API_KEY=your_key
    export GITLAB_TOKEN=your_gitlab_pat

    # Esegui per GitLab MR
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

## Cosa Fare Dopo?

| Compito | Documento |
|---------|-----------|
| Configurare la lingua | [Configurazione](configuration.md) |
| Ottimizzare per GitHub | [Guida GitHub](github.md) |
| Ottimizzare per GitLab | [Guida GitLab](gitlab.md) |
| Vedere esempi | [Esempi](examples/index.md) |

---

## Esempio di Risultato

Dopo l'esecuzione, vedrai commenti inline:

![Esempio AI Review](https://via.placeholder.com/800x400?text=AI+Review+Inline+Comment)

Ogni commento contiene:

- :red_circle: / :yellow_circle: / :blue_circle: Badge di gravita
- Descrizione del problema
- Pulsante **"Apply suggestion"**
- Spiegazione espandibile "Perche e importante?"

---

## Troubleshooting

### La revisione non appare?

1. Controlla i log del job CI
2. Verifica che `GOOGLE_API_KEY` sia corretta
3. Per GitHub: controlla `permissions: pull-requests: write`
4. Per PR da fork: i secret non sono disponibili

### Rate limit?

Gemini free tier: 15 RPM. Aspetta un minuto.

:point_right: [Tutti i problemi →](troubleshooting.md)
