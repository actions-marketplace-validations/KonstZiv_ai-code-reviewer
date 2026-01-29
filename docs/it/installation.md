# Installazione

L'opzione di installazione dipende dal tuo caso d'uso e obiettivi.

---

## 1. CI/CD — Revisione Automatica {#ci-cd}

Lo scenario piu comune: AI Code Reviewer viene eseguito automaticamente quando un PR/MR viene creato o aggiornato.

### GitHub Actions

Il modo piu semplice per GitHub — usa la GitHub Action pronta all'uso:

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

**Configurazione necessaria:**

| Cosa serve | Dove configurare |
|------------|------------------|
| `GOOGLE_API_KEY` | Repository → Settings → Secrets → Actions |

:point_right: [Esempio completo con concurrency e filtering →](quick-start.md#github-actions)

:point_right: [Guida dettagliata GitHub →](github.md)

---

### GitLab CI

Per GitLab, usa l'immagine Docker in `.gitlab-ci.yml`:

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

**Configurazione necessaria:**

| Cosa serve | Dove configurare |
|------------|------------------|
| `GOOGLE_API_KEY` | Project → Settings → CI/CD → Variables (Masked) |
| `GITLAB_TOKEN` | Opzionale, per commenti inline ([dettagli](gitlab.md#tokens)) |

:point_right: [Esempio completo →](quick-start.md#gitlab-ci)

:point_right: [Guida dettagliata GitLab →](gitlab.md)

---

## 2. Test Locale / Valutazione {#local}

### Perche serve?

1. **Valutazione prima del deployment** — prova su un PR reale prima di aggiungerlo alla CI
2. **Debugging** — se qualcosa non funziona in CI, esegui localmente con `--log-level DEBUG`
3. **Revisione retrospettiva** — analizza un vecchio PR/MR
4. **Demo** — mostra al team/management come funziona

### Come funziona

```
Terminale locale
       │
       ▼
   ai-review CLI
       │
       ├──► GitHub/GitLab API (legge PR/MR, diff, issue collegati)
       │
       ├──► Gemini API (ottiene revisione)
       │
       └──► GitHub/GitLab API (pubblica commenti)
```

### Variabili d'Ambiente Necessarie

| Variabile | Descrizione | Quando serve | Come ottenerla |
|-----------|-------------|--------------|----------------|
| `GOOGLE_API_KEY` | Chiave API Gemini | **Sempre** | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Per GitHub | [Istruzioni](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab Personal Access Token | Per GitLab | [Istruzioni](gitlab.md#get-token) |

---

### Opzione A: Docker (consigliato)

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

---

### Opzione B: pip / uv

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

### Variabili Opzionali

Variabili aggiuntive disponibili per la personalizzazione:

| Variabile | Default | Effetto |
|-----------|---------|---------|
| `LANGUAGE` | `en` | Lingua delle risposte (ISO 639) |
| `LANGUAGE_MODE` | `adaptive` | Modalita di rilevamento lingua |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Modello Gemini |
| `LOG_LEVEL` | `INFO` | Livello di logging |

:point_right: [Lista completa delle variabili →](configuration.md#optional)

---

## 3. Ambiente Corporate (air-gapped) {#airgapped}

Per ambienti con accesso internet limitato.

### Limitazioni

!!! warning "Accesso API Gemini necessario"
    AI Code Reviewer usa Google Gemini API per l'analisi del codice.

    **Accesso necessario a:** `generativelanguage.googleapis.com`

    Il supporto per modelli LLM deployati localmente **non e ancora implementato**.

### Deployment Immagine Docker

**Passo 1: Su una macchina con accesso internet**

```bash
# Scarica l'immagine
docker pull ghcr.io/konstziv/ai-code-reviewer:1

# Salva su file
docker save ghcr.io/konstziv/ai-code-reviewer:1 > ai-code-reviewer.tar
```

**Passo 2: Trasferisci il file nell'ambiente chiuso**

**Passo 3: Carica nel registry interno**

```bash
# Carica da file
docker load < ai-code-reviewer.tar

# Re-tag per il registry interno
docker tag ghcr.io/konstziv/ai-code-reviewer:1 \
    registry.internal.company.com/devops/ai-code-reviewer:1

# Push
docker push registry.internal.company.com/devops/ai-code-reviewer:1
```

**Passo 4: Usa in GitLab CI**

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

## 4. Contributor / Sviluppo {#development}

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
