# Installazione

L'opzione di installazione dipende dal tuo caso d'uso e obiettivi.

---

## 1. CI/CD — Revisione Automatica {#ci-cd}

Lo scenario piu comune: AI Code Reviewer viene eseguito automaticamente quando un PR/MR viene creato o aggiornato.

Configurazione in 5 minuti:

- :octicons-mark-github-16: **[Configurazione review per GitHub →](quick-start.md)**

    :point_right: [Esempi workflows →](examples/github-minimal.md) · [Guida dettagliata GitHub →](github.md)

- :simple-gitlab: **[Configurazione review per GitLab →](quick-start.md)**

    :point_right: [Esempi workflows →](examples/gitlab-minimal.md) · [Guida dettagliata GitLab →](gitlab.md)

Per configurazione avanzata vedi [Configurazione →](configuration.md)

---

## 2. Distribuzione Autonoma: CLI/Docker {#standalone}

CLI e Docker image permettono di eseguire AI Code Reviewer al di fuori della pipeline CI standard.

### Scenari di utilizzo

| Scenario | Come realizzare |
|----------|-----------------|
| **Esecuzione manuale** | Terminale locale — debugging, demo, valutazione |
| **Scheduled review** | GitLab Scheduled Pipeline / GitHub Actions `schedule` / cron |
| **Batch review** | Script che itera sui PR/MR aperti |
| **Server proprio** | Docker su server con accesso alle Git API |
| **On-demand review** | Webhook → avvio container |

### Variabili d'ambiente obbligatorie

| Variabile | Descrizione | Quando serve | Come ottenerla |
|-----------|-------------|--------------|----------------|
| `GOOGLE_API_KEY` | Chiave API Gemini | **Sempre** | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Per GitHub | [Istruzioni](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab Personal Access Token | Per GitLab | [Istruzioni](gitlab.md#get-token) |

---

### Esecuzione Manuale

Per debugging, demo, valutazione prima del deployment, analisi retrospettiva di PR/MR.

#### Docker (consigliato)

Non serve installare Python — tutto e nel container.

**Passo 1: Scarica l'immagine**

```bash
docker pull ghcr.io/konstziv/ai-code-reviewer:1
```

**Passo 2: Esegui la revisione**

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

!!! tip "Immagini Docker"
    Disponibili da due registry:

    - `ghcr.io/konstziv/ai-code-reviewer:1` — GitHub Container Registry
    - `koszivdocker/ai-reviewbot:1` — DockerHub

#### pip / uv

Installazione come pacchetto Python.

**Passo 1: Installa**

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

!!! note "Versione Python"
    Richiede Python **3.13+**

**Passo 2: Configura le variabili**

```bash
export GOOGLE_API_KEY=your_api_key
export GITHUB_TOKEN=your_token  # o GITLAB_TOKEN per GitLab
```

**Passo 3: Esegui**

=== "GitHub PR"

    ```bash
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab MR"

    ```bash
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

### Variabili opzionali

Variabili aggiuntive disponibili per la personalizzazione:

| Variabile | Default | Effetto |
|-----------|---------|---------|
| `LANGUAGE` | `en` | Lingua delle risposte (ISO 639) |
| `LANGUAGE_MODE` | `adaptive` | Modalita di rilevamento lingua |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Modello Gemini |
| `LOG_LEVEL` | `INFO` | Livello di logging |

:point_right: [Lista completa delle variabili →](configuration.md#optional)

---

### Scheduled reviews

Esecuzione review su base programmata — per risparmiare risorse o quando non serve feedback immediato.

=== "GitLab Scheduled Pipeline"

    ```yaml
    # .gitlab-ci.yml
    ai-review-scheduled:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      script:
        - |
          # Ottieni lista MR aperti
          MR_LIST=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
            "$CI_SERVER_URL/api/v4/projects/$CI_PROJECT_ID/merge_requests?state=opened" \
            | jq -r '.[].iid')

          # Esegui review per ogni MR
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

    **Configurazione schedule:** Project → Build → Pipeline schedules → New schedule

=== "GitHub Actions Schedule"

    ```yaml
    # .github/workflows/scheduled-review.yml
    name: Scheduled AI Review

    on:
      schedule:
        - cron: '0 9 * * *'  # Ogni giorno alle 9:00 UTC

    jobs:
      review-open-prs:
        runs-on: ubuntu-latest
        steps:
          - name: Get open PRs and review
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
            run: |
              # Ottieni lista PR aperti
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

### Server proprio / ambiente privato

Per deployment su infrastruttura propria con accesso alle Git API.

**Opzioni:**

- **Docker su server** — esecuzione tramite cron, systemd timer, o come servizio
- **Kubernetes** — CronJob per scheduled reviews
- **Self-hosted GitLab** — aggiungi variabile `GITLAB_URL` (vedi esempio sotto)

**Esempio cron job:**

```bash
# /etc/cron.d/ai-review
# Ogni giorno alle 10:00 esegui review per tutti gli MR aperti
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
    Per self-hosted GitLab aggiungi variabile `GITLAB_URL`:

    ```bash
    -e GITLAB_URL=https://gitlab.company.com
    ```

---

## 3. Contributor / Sviluppo {#development}

Se hai tempo e ispirazione per aiutare a sviluppare il pacchetto, o vuoi usarlo come base per il tuo sviluppo — accogliamo e incoraggiamo sinceramente tali azioni!

### Installazione per Sviluppo

```bash
# Clona il repository
git clone https://github.com/KonstZiv/ai-code-reviewer.git
cd ai-code-reviewer

# Installa le dipendenze (usiamo uv)
uv sync

# Verifica
uv run ai-review --help

# Esegui i test
uv run pytest

# Esegui i controlli di qualita
uv run ruff check .
uv run mypy .
```

!!! info "uv"
    Usiamo [uv](https://github.com/astral-sh/uv) per la gestione delle dipendenze.

    Installa: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Struttura del Progetto

```
ai-code-reviewer/
├── src/ai_reviewer/      # Codice sorgente
│   ├── core/             # Modelli, config, formattazione
│   ├── integrations/     # GitHub, GitLab, Gemini
│   └── utils/            # Utility
├── tests/                # Test
├── docs/                 # Documentazione
└── examples/             # Esempi di configurazione CI
```

:point_right: [Come contribuire →](https://github.com/KonstZiv/ai-code-reviewer/blob/main/CONTRIBUTING.md)

---

## Requisiti {#requirements}

### Requisiti di Sistema

| Componente | Requisito |
|------------|-----------|
| Python | 3.13+ (per pip install) |
| Docker | 20.10+ (per Docker) |
| OS | Linux, macOS, Windows |
| RAM | 256MB+ |
| Rete | Accesso a `generativelanguage.googleapis.com` |

### Chiavi API

| Chiave | Necessaria | Come ottenerla |
|--------|------------|----------------|
| Google Gemini API | **Si** | [Google AI Studio](https://aistudio.google.com/) |
| GitHub PAT | Per GitHub | [Istruzioni](github.md#get-token) |
| GitLab PAT | Per GitLab | [Istruzioni](gitlab.md#get-token) |

### Limiti API Gemini

!!! info "Free tier"
    Google Gemini ha un free tier:

    | Limite | Valore |
    |--------|--------|
    | Richieste per minuto | 15 RPM |
    | Token al giorno | 1M |
    | Richieste al giorno | 1500 |

    Questo e sufficiente per la maggior parte dei progetti.

---

## Prossimo Passo

:point_right: [Quick Start →](quick-start.md)
