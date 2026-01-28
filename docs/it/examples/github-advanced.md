# GitHub: Esempio Avanzato

Configurazione pronta per produzione con tutte le best practice.

---

## Passo 1: Aggiungi un Secret

`Settings → Secrets and variables → Actions → New repository secret`

| Nome | Valore |
|------|--------|
| `GOOGLE_API_KEY` | La tua chiave API Gemini |

---

## Passo 2: Crea il File

`.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
    # Opzionale: filtro file
    # paths:
    #   - '**.py'
    #   - '**.js'
    #   - '**.ts'

# Cancella esecuzione precedente con nuovo commit
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    name: AI Review
    runs-on: ubuntu-latest

    # Non eseguire per PR da fork (secret non disponibili)
    if: github.event.pull_request.head.repo.full_name == github.repository

    # Non bloccare PR se la revisione fallisce
    continue-on-error: true

    # Protezione timeout
    timeout-minutes: 10

    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Run AI Code Review
        uses: KonstZiv/ai-code-reviewer@v1
        with:
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
          language: uk
          language_mode: adaptive
          log_level: INFO
```

---

## Cosa Include

| Funzionalita | Stato | Descrizione |
|--------------|-------|-------------|
| Commenti inline | :white_check_mark: | Con Apply Suggestion |
| Concurrency | :white_check_mark: | Cancella vecchie esecuzioni |
| Filtro fork | :white_check_mark: | Salta PR da fork |
| Timeout | :white_check_mark: | Massimo 10 minuti |
| Non bloccante | :white_check_mark: | PR non bloccato |
| Lingua personalizzata | :white_check_mark: | `language: uk` |

---

## Variazioni

### Con Filtro File

```yaml
on:
  pull_request:
    paths:
      - 'src/**'
      - '**.py'
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Con Filtro Branch

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

### Con Modello Personalizzato

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    gemini_model: gemini-1.5-pro  # Modello piu potente
```

### Con Log DEBUG

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    log_level: DEBUG
```

---

## Opzioni Action

| Input | Descrizione | Default |
|-------|-------------|---------|
| `google_api_key` | Chiave API Gemini | **necessario** |
| `github_token` | Token GitHub | `${{ github.token }}` |
| `language` | Lingua risposte | `en` |
| `language_mode` | `adaptive` / `fixed` | `adaptive` |
| `gemini_model` | Modello Gemini | `gemini-2.0-flash` |
| `log_level` | Livello log | `INFO` |

---

## Troubleshooting

### La Revisione Non Appare

1. Controlla i log del workflow
2. Controlla che non sia un PR da fork
3. Controlla `permissions: pull-requests: write`

### Rate Limit

La concurrency cancella automaticamente le vecchie esecuzioni, riducendo il carico.

---

## Prossimo Passo

:point_right: [Esempi GitLab →](gitlab-minimal.md)
