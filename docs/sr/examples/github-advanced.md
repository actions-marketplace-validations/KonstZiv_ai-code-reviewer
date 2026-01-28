# GitHub: Napredni primjer

Konfiguracija spremna za produkciju sa svim najboljim praksama.

---

## Korak 1: Dodajte tajnu

`Settings → Secrets and variables → Actions → New repository secret`

| Ime | Vrijednost |
|------|-------|
| `GOOGLE_API_KEY` | Vaš Gemini API ključ |

---

## Korak 2: Kreirajte fajl

`.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
    # Opciono: filter fajlova
    # paths:
    #   - '**.py'
    #   - '**.js'
    #   - '**.ts'

# Otkaži prethodni run na novi commit
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    name: AI Review
    runs-on: ubuntu-latest

    # Ne pokreći za fork PR-ove (tajne nijesu dostupne)
    if: github.event.pull_request.head.repo.full_name == github.repository

    # Ne blokiraj PR ako revizija ne uspije
    continue-on-error: true

    # Zaštita timeout-om
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

## Šta je uključeno

| Funkcionalnost | Status | Opis |
|---------|--------|-------------|
| Inline komentari | :white_check_mark: | Sa Apply Suggestion |
| Konkurentnost | :white_check_mark: | Otkazuje stare pokretanja |
| Fork filter | :white_check_mark: | Preskače fork PR-ove |
| Timeout | :white_check_mark: | Maksimalno 10 minuta |
| Neblokirajući | :white_check_mark: | PR nije blokiran |
| Prilagođeni jezik | :white_check_mark: | `language: uk` |

---

## Varijacije

### Sa filterom fajlova

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

### Sa filterom grana

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

### Sa prilagođenim modelom

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    gemini_model: gemini-1.5-pro  # Moćniji model
```

### Sa DEBUG logovima

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    log_level: DEBUG
```

---

## Opcije Action-a

| Input | Opis | Podrazumijevano |
|-------|-------------|---------|
| `google_api_key` | Gemini API ključ | **obavezno** |
| `github_token` | GitHub token | `${{ github.token }}` |
| `language` | Jezik odgovora | `en` |
| `language_mode` | `adaptive` / `fixed` | `adaptive` |
| `gemini_model` | Gemini model | `gemini-2.0-flash` |
| `log_level` | Nivo logova | `INFO` |

---

## Rješavanje problema

### Revizija se ne pojavljuje

1. Provjerite logove workflow-a
2. Provjerite da nije fork PR
3. Provjerite `permissions: pull-requests: write`

### Rate Limit

Konkurentnost automatski otkazuje stara pokretanja, smanjujući opterećenje.

---

## Sljedeći korak

:point_right: [GitLab primjeri →](gitlab-minimal.md)
