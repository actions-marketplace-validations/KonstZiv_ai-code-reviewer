# GitLab: Minimalni primjer

Najjednostavnija konfiguracija za GitLab CI.

---

## Korak 1: Dodajte varijablu

`Settings → CI/CD → Variables → Add variable`

| Ime | Vrijednost | Opcije |
|------|-------|---------|
| `GOOGLE_API_KEY` | Vaš Gemini API ključ | Masked |

---

## Korak 2: Dodajte job

`.gitlab-ci.yml`:

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

---

## Korak 3: Kreirajte MR

Gotovo! AI revizija će se pojaviti kao komentari na MR-u.

---

## Šta je uključeno

| Funkcionalnost | Status |
|---------|--------|
| Bilješke na MR | :white_check_mark: |
| Jezička adaptivnost | :white_check_mark: (adaptive) |
| Metrike | :white_check_mark: |
| Auto-retry | :white_check_mark: |

---

## Ograničenja

| Ograničenje | Rješenje |
|------------|----------|
| MR blokiran na grešci | Dodajte `allow_failure: true` |

---

## Sljedeći korak

:point_right: [Napredni primjer →](gitlab-advanced.md)
