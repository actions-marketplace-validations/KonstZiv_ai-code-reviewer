# Instalacija

Opcija instalacije zavisi od vašeg slučaja upotrebe i ciljeva.

---

## 1. CI/CD — Automatizovana revizija {#ci-cd}

Najčešći scenario: AI Code Reviewer se pokreće automatski kada se kreira ili ažurira PR/MR.

Podesite za 5 minuta:

- :octicons-mark-github-16: **[Podešavanje revizije za GitHub →](quick-start.md)**

    :point_right: [Primjeri workflow-a →](examples/github-minimal.md) · [Detaljan GitHub vodič →](github.md)

- :simple-gitlab: **[Podešavanje revizije za GitLab →](quick-start.md)**

    :point_right: [Primjeri workflow-a →](examples/gitlab-minimal.md) · [Detaljan GitLab vodič →](gitlab.md)

Za fino podešavanje pogledajte [Konfiguracija →](configuration.md)

---

## 2. Samostalno postavljanje: CLI/Docker {#standalone}

CLI i Docker image omogućavaju pokretanje AI Code Reviewer-a van standardnog CI pipeline-a.

### Scenariji upotrebe

| Scenario | Kako realizovati |
|----------|------------------|
| **Ručno pokretanje** | Lokalni terminal — debugging, demo, evaluacija |
| **Scheduled review** | GitLab Scheduled Pipeline / GitHub Actions `schedule` / cron |
| **Batch review** | Skripta koja iterira kroz otvorene PR/MR |
| **Vlastiti server** | Docker na serveru sa pristupom Git API-ju |
| **On-demand review** | Webhook → pokretanje kontejnera |

### Obavezne varijable okruženja

| Varijabla | Opis | Kada je potrebna | Kako dobiti |
|----------|------|------------------|-------------|
| `GOOGLE_API_KEY` | API ključ za Gemini | **Uvijek** | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Za GitHub | [Instrukcije](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab Personal Access Token | Za GitLab | [Instrukcije](gitlab.md#get-token) |

---

### Ručno pokretanje

Za debugging, demo, evaluaciju prije implementacije, retrospektivnu analizu PR/MR.

#### Docker (preporučeno)

Nije potrebna instalacija Python-a — sve je u kontejneru.

**Korak 1: Preuzmite image**

```bash
docker pull ghcr.io/konstziv/ai-code-reviewer:1
```

**Korak 2: Pokrenite reviziju**

=== "GitHub PR"

    ```bash
    docker run --rm \
      -e GOOGLE_API_KEY=your_api_key \
      -e GITHUB_TOKEN=your_token \
      ghcr.io/konstziv/ai-code-reviewer:1 \
      --repo owner/repo --pr-number 123
    ```

=== "GitLab MR"

    ```bash
    docker run --rm \
      -e GOOGLE_API_KEY=your_api_key \
      -e GITLAB_TOKEN=your_token \
      ghcr.io/konstziv/ai-code-reviewer:1 \
      --provider gitlab --project owner/repo --mr-iid 123
    ```

!!! tip "Docker images"
    Dostupni iz dva registra:

    - `ghcr.io/konstziv/ai-code-reviewer:1` — GitHub Container Registry
    - `koszivdocker/ai-reviewbot:1` — DockerHub

#### pip / uv

Instalacija kao Python paket.

**Korak 1: Instalirajte**

=== "pip"

    ```bash
    pip install ai-reviewbot
    ```

=== "uv"

    ```bash
    uv tool install ai-code-reviewer
    ```

=== "pipx"

    ```bash
    pipx install ai-code-reviewer
    ```

!!! note "Python verzija"
    Zahtijeva Python **3.13+**

**Korak 2: Podesite varijable**

```bash
export GOOGLE_API_KEY=your_api_key
export GITHUB_TOKEN=your_token  # ili GITLAB_TOKEN za GitLab
```

**Korak 3: Pokrenite**

=== "GitHub PR"

    ```bash
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab MR"

    ```bash
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

### Opcione varijable

Dodatne varijable su dostupne za fino podešavanje:

| Varijabla | Podrazumijevano | Efekat |
|----------|---------|--------|
| `LANGUAGE` | `en` | Jezik odgovora (ISO 639) |
| `LANGUAGE_MODE` | `adaptive` | Režim detekcije jezika |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model |
| `LOG_LEVEL` | `INFO` | Nivo logovanja |

:point_right: [Puna lista varijabli →](configuration.md#optional)

---

### Scheduled reviews

Pokretanje revizije po rasporedu — za uštedu resursa ili kada nije potreban trenutni feedback.

=== "GitLab Scheduled Pipeline"

    ```yaml
    # .gitlab-ci.yml
    ai-review-scheduled:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      script:
        - |
          # Dobij listu otvorenih MR
          MR_LIST=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
            "$CI_SERVER_URL/api/v4/projects/$CI_PROJECT_ID/merge_requests?state=opened" \
            | jq -r '.[].iid')

          # Pokreni reviziju za svaki MR
          for MR_IID in $MR_LIST; do
            echo "Reviewing MR !$MR_IID"
            ai-review --provider gitlab --project $CI_PROJECT_PATH --pr $MR_IID || true
          done
      rules:
        - if: $CI_PIPELINE_SOURCE == "schedule"
      variables:
        GOOGLE_API_KEY: $GOOGLE_API_KEY
        GITLAB_TOKEN: $GITLAB_TOKEN
    ```

    **Podešavanje rasporeda:** Project → Build → Pipeline schedules → New schedule

=== "GitHub Actions Schedule"

    ```yaml
    # .github/workflows/scheduled-review.yml
    name: Scheduled AI Review

    on:
      schedule:
        - cron: '0 9 * * *'  # Svaki dan u 9:00 UTC

    jobs:
      review-open-prs:
        runs-on: ubuntu-latest
        steps:
          - name: Get open PRs and review
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
            run: |
              # Dobij listu otvorenih PR
              PRS=$(gh pr list --repo ${{ github.repository }} --state open --json number -q '.[].number')

              for PR in $PRS; do
                echo "Reviewing PR #$PR"
                docker run --rm \
                  -e GOOGLE_API_KEY -e GITHUB_TOKEN \
                  ghcr.io/konstziv/ai-code-reviewer:1 \
                  --repo ${{ github.repository }} --pr $PR || true
              done
    ```

---

### Vlastiti server / privatno okruženje

Za deployovanje na vlastitoj infrastrukturi sa pristupom Git API-ju.

**Opcije:**

- **Docker na serveru** — pokretanje putem cron, systemd timer, ili kao servis
- **Kubernetes** — CronJob za scheduled reviews
- **Self-hosted GitLab** — dodajte varijablu `GITLAB_URL` (pogledajte primjer ispod)

**Primjer cron job-a:**

```bash
# /etc/cron.d/ai-review
# Svaki dan u 10:00 pokreni reviziju za sve otvorene MR
0 10 * * * reviewer /usr/local/bin/review-all-mrs.sh
```

```bash
#!/bin/bash
# /usr/local/bin/review-all-mrs.sh
export GOOGLE_API_KEY="your_key"
export GITLAB_TOKEN="your_token"

MR_LIST=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.company.com/api/v4/projects/123/merge_requests?state=opened" \
  | jq -r '.[].iid')

for MR_IID in $MR_LIST; do
  docker run --rm \
    -e GOOGLE_API_KEY -e GITLAB_TOKEN \
    ghcr.io/konstziv/ai-code-reviewer:1 \
    --provider gitlab --project group/repo --pr $MR_IID
done
```

!!! tip "Self-hosted GitLab"
    Za self-hosted GitLab dodajte varijablu `GITLAB_URL`:

    ```bash
    -e GITLAB_URL=https://gitlab.company.com
    ```

---

## 3. Kontributori / Razvoj {#development}

Ako imate vremena i inspiracije da pomognete u razvoju paketa, ili želite da ga koristite kao osnovu za sopstveni razvoj — iskreno pozdravljamo i ohrabrujemo takve akcije!

### Razvojna instalacija

```bash
# Klonirajte repozitorijum
git clone https://github.com/KonstZiv/ai-code-reviewer.git
cd ai-code-reviewer

# Instalirajte zavisnosti (koristimo uv)
uv sync

# Verifikujte
uv run ai-review --help

# Pokrenite testove
uv run pytest

# Pokrenite provjere kvaliteta
uv run ruff check .
uv run mypy .
```

!!! info "uv"
    Koristimo [uv](https://github.com/astral-sh/uv) za upravljanje zavisnostima.

    Instalirajte: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Struktura projekta

```
ai-code-reviewer/
├── src/ai_reviewer/      # Izvorni kod
│   ├── core/             # Modeli, konfiguracija, formatiranje
│   ├── integrations/     # GitHub, GitLab, Gemini
│   └── utils/            # Pomoćne funkcije
├── tests/                # Testovi
├── docs/                 # Dokumentacija
└── examples/             # Primjeri CI konfiguracija
```

:point_right: [Kako doprinijeti →](https://github.com/KonstZiv/ai-code-reviewer/blob/main/CONTRIBUTING.md)

---

## Zahtjevi {#requirements}

### Sistemski zahtjevi

| Komponenta | Zahtjev |
|-----------|-------------|
| Python | 3.13+ (za pip instalaciju) |
| Docker | 20.10+ (za Docker) |
| OS | Linux, macOS, Windows |
| RAM | 256MB+ |
| Mreža | Pristup `generativelanguage.googleapis.com` |

### API ključevi

| Ključ | Potreban | Kako dobiti |
|-----|----------|------------|
| Google Gemini API | **Da** | [Google AI Studio](https://aistudio.google.com/) |
| GitHub PAT | Za GitHub | [Instrukcije](github.md#get-token) |
| GitLab PAT | Za GitLab | [Instrukcije](gitlab.md#get-token) |

### Ograničenja Gemini API-ja

!!! info "Besplatni nivo"
    Google Gemini ima besplatni nivo:

    | Ograničenje | Vrijednost |
    |-------|-------|
    | Zahtjevi po minuti | 15 RPM |
    | Tokeni po danu | 1M |
    | Zahtjevi po danu | 1500 |

    Ovo je dovoljno za većinu projekata.

---

## Sljedeći korak

:point_right: [Brzi početak →](quick-start.md)
