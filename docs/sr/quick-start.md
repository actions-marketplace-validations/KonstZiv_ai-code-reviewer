# Brzi početak

Pokrenite AI Code Reviewer za 1 minut.

---

## GitHub Actions

### Korak 1: Dodajte tajnu

`Settings → Secrets and variables → Actions → New repository secret`

| Ime | Vrijednost |
|------|-------|
| `GOOGLE_API_KEY` | Vaš Gemini API ključ |

:point_right: [Preuzmite ključ](https://aistudio.google.com/)

### Korak 2: Kreirajte workflow

U korijenu vašeg projekta, kreirajte fajl `.github/workflows/ai-review.yml`

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
    # Ne pokreći za fork PR-ove (nema pristupa tajnama)
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

### Korak 3: Kreirajte PR

Gotovo! AI revizija će se pojaviti automatski.

---

## GitLab CI

### Korak 1: Dodajte varijablu

`Settings → CI/CD → Variables`

| Ime | Vrijednost | Opcije |
|------|-------|---------|
| `GOOGLE_API_KEY` | Vaš Gemini API ključ | Masked, Protected |

:point_right: [Preuzmite ključ](https://aistudio.google.com/)

### Korak 2: Dodajte job

U korijenu vašeg projekta, kreirajte fajl `.gitlab-ci.yml`

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

!!! note "Za inline komentare"
    `CI_JOB_TOKEN` ima ograničenja. Za punu funkcionalnost koristite [Personal Access Token](gitlab.md#personal-access-token).

### Korak 3: Kreirajte MR

Gotovo! AI revizija će se pojaviti kao komentari na MR-u.

---

## Lokalno pokretanje

Za lokalno testiranje trebate:

- **GOOGLE_API_KEY** — [preuzmite na Google AI Studio](https://aistudio.google.com/)
- **GITHUB_TOKEN** ili **GITLAB_TOKEN** — zavisno od platforme:
    - GitHub: [kako dobiti PAT](github.md#get-token)
    - GitLab: [kako dobiti PAT](gitlab.md#get-token)

=== "GitHub"

    ```bash
    # Instalirajte
    pip install ai-reviewbot

    # Konfigurišite
    export GOOGLE_API_KEY=your_key
    export GITHUB_TOKEN=your_github_pat

    # Pokrenite za GitHub PR
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab"

    ```bash
    # Instalirajte
    pip install ai-reviewbot

    # Konfigurišite
    export GOOGLE_API_KEY=your_key
    export GITLAB_TOKEN=your_gitlab_pat

    # Pokrenite za GitLab MR
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

## Šta dalje?

| Zadatak | Dokument |
|------|----------|
| Konfiguriši jezik | [Konfiguracija](configuration.md) |
| Optimizuj za GitHub | [GitHub vodič](github.md) |
| Optimizuj za GitLab | [GitLab vodič](gitlab.md) |
| Pogledaj primjere | [Primjeri](examples/index.md) |

---

## Primjer rezultata

Nakon pokretanja, vidjećete inline komentare:

![AI Review primjer](https://via.placeholder.com/800x400?text=AI+Review+Inline+Comment)

Svaki komentar sadrži:

- :red_circle: / :yellow_circle: / :blue_circle: Oznaku ozbiljnosti
- Opis problema
- **"Apply suggestion"** dugme
- Sklopivi odjeljak "Zašto je ovo važno?" sa objašnjenjem

---

## Rješavanje problema

### Revizija se ne pojavljuje?

1. Provjerite logove CI job-a
2. Verifikujte da je `GOOGLE_API_KEY` ispravan
3. Za GitHub: provjerite `permissions: pull-requests: write`
4. Za fork PR-ove: tajne nijesu dostupne

### Rate limit?

Gemini besplatni nivo: 15 RPM. Sačekajte minut.

:point_right: [Svi problemi →](troubleshooting.md)
