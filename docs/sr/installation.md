# Instalacija

Opcija instalacije zavisi od vašeg slučaja upotrebe i ciljeva.

---

## 1. CI/CD — Automatizovana revizija {#ci-cd}

Najčešći scenario: AI Code Reviewer se pokreće automatski kada se kreira ili ažurira PR/MR.

### GitHub Actions

Najjednostavniji način za GitHub — koristite gotov GitHub Action:

```yaml
# .github/workflows/ai-review.yml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

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

**Potrebna podešavanja:**

| Šta je potrebno | Đe se konfiguriše |
|---------------|-------------------|
| `GOOGLE_API_KEY` | Repository → Settings → Secrets → Actions |

:point_right: [Puni primjer sa konkurentnošću i filterima →](quick-start.md#github-actions)

:point_right: [Detaljan GitHub vodič →](github.md)

---

### GitLab CI

Za GitLab, koristite Docker image u `.gitlab-ci.yml`:

```yaml
# .gitlab-ci.yml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

**Potrebna podešavanja:**

| Šta je potrebno | Đe se konfiguriše |
|---------------|-------------------|
| `GOOGLE_API_KEY` | Project → Settings → CI/CD → Variables (Masked) |
| `GITLAB_TOKEN` | Opciono, za inline komentare ([detalji](gitlab.md#tokens)) |

:point_right: [Puni primjer →](quick-start.md#gitlab-ci)

:point_right: [Detaljan GitLab vodič →](gitlab.md)

---

## 2. Lokalno testiranje / Evaluacija {#local}

### Zašto je ovo potrebno?

1. **Evaluacija prije deployovanja** — isprobajte na pravom PR-u prije dodavanja u CI
2. **Debagovanje** — ako nešto ne radi u CI-ju, pokrenite lokalno sa `--log-level DEBUG`
3. **Retrospektivna revizija** — analizirajte stari PR/MR
4. **Demo** — pokažite timu/menadžmentu kako funkcioniše

### Kako funkcioniše

```
Lokalni terminal
       │
       ▼
   ai-review CLI
       │
       ├──► GitHub/GitLab API (čita PR/MR, diff, povezane issue-e)
       │
       ├──► Gemini API (dobija reviziju)
       │
       └──► GitHub/GitLab API (objavljuje komentare)
```

### Potrebne varijable okruženja

| Varijabla | Opis | Kada je potrebna | Kako dobiti |
|----------|-------------|-------------|------------|
| `GOOGLE_API_KEY` | Gemini API ključ | **Uvijek** | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Za GitHub | [Instrukcije](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab Personal Access Token | Za GitLab | [Instrukcije](gitlab.md#get-token) |

---

### Opcija A: Docker (preporučeno)

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

---

### Opcija B: pip / uv

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

## 3. Korporativno okruženje (air-gapped) {#airgapped}

Za okruženja sa ograničenim pristupom internetu.

### Ograničenja

!!! warning "Potreban pristup Gemini API-ju"
    AI Code Reviewer koristi Google Gemini API za analizu koda.

    **Potreban pristup:** `generativelanguage.googleapis.com`

    Podrška za lokalno deployovane LLM modele **još nije implementirana**.

### Deployovanje Docker image-a

**Korak 1: Na mašini sa pristupom internetu**

```bash
# Preuzmite image
docker pull ghcr.io/konstziv/ai-code-reviewer:1

# Sačuvajte u fajl
docker save ghcr.io/konstziv/ai-code-reviewer:1 > ai-code-reviewer.tar
```

**Korak 2: Prenesite fajl u zatvoreno okruženje**

**Korak 3: Učitajte u interni registar**

```bash
# Učitajte iz fajla
docker load < ai-code-reviewer.tar

# Ponovo tagirajte za interni registar
docker tag ghcr.io/konstziv/ai-code-reviewer:1 \
    registry.internal.company.com/devops/ai-code-reviewer:1

# Push
docker push registry.internal.company.com/devops/ai-code-reviewer:1
```

**Korak 4: Koristite u GitLab CI**

```yaml
ai-review:
  image: registry.internal.company.com/devops/ai-code-reviewer:1
  script:
    - ai-review
  variables:
    GITLAB_URL: https://gitlab.internal.company.com
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

---

## 4. Kontributori / Razvoj {#development}

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
