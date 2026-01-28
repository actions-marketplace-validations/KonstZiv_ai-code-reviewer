# GitHub: Minimalni primjer

Najjednostavnija konfiguracija za GitHub Actions.

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

## Korak 3: Kreirajte PR

Gotovo! AI revizija će se pojaviti automatski.

---

## Šta je uključeno

| Funkcionalnost | Status |
|---------|--------|
| Inline komentari | :white_check_mark: |
| Apply Suggestion dugme | :white_check_mark: |
| Jezička adaptivnost | :white_check_mark: (adaptive) |
| Metrike | :white_check_mark: |

---

## Ograničenja

| Ograničenje | Rješenje |
|------------|----------|
| Fork PR-ovi ne rade | Očekivano ponašanje |
| Nema konkurentnosti | Pogledajte [napredni primjer](github-advanced.md) |
| Engleski po default-u | Dodajte `language: uk` |

---

## Sljedeći korak

:point_right: [Napredni primjer →](github-advanced.md)
