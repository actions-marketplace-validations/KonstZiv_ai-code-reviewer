# GitHub: Esempio Minimo

La configurazione piu semplice per GitHub Actions.

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
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

---

## Passo 3: Crea un PR

Fatto! La revisione AI apparira automaticamente.

---

## Cosa Include

| Funzionalita | Stato |
|--------------|-------|
| Commenti inline | :white_check_mark: |
| Pulsante Apply Suggestion | :white_check_mark: |
| Adattivita linguistica | :white_check_mark: (adaptive) |
| Metriche | :white_check_mark: |

---

## Limitazioni

| Limitazione | Soluzione |
|-------------|-----------|
| PR da fork non funzionano | Comportamento previsto |
| Nessuna concurrency | Vedi [esempio avanzato](github-advanced.md) |
| Inglese di default | Aggiungi `language: it` |

---

## Prossimo Passo

:point_right: [Esempio avanzato →](github-advanced.md)
