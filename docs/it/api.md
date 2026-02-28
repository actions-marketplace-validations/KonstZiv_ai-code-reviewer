# Riferimento CLI

Riferimento comandi di AI Code Reviewer.

---

## Comando Principale

```bash
ai-review [OPTIONS]
```

**Comportamento:**

- In CI (GitHub Actions / GitLab CI) — rileva automaticamente il contesto
- Manualmente — bisogna specificare `--provider`, `--repo`, `--pr`

!!! info "Subcommand"
    `ai-review` (senza subcommand) esegue una review — retrocompatibile. Usa `ai-review discover` per eseguire il discovery standalone.

---

## Opzioni

| Opzione | Abbreviazione | Descrizione | Default |
|---------|---------------|-------------|---------|
| `--provider` | `-p` | Provider CI | Auto-detect |
| `--repo` | `-r` | Repository (owner/repo) | Auto-detect |
| `--pr` | | Numero PR/MR | Auto-detect |
| `--help` | | Mostra aiuto | |
| `--version` | | Mostra versione | |

---

## Provider

| Valore | Descrizione |
|--------|-------------|
| `github` | GitHub (GitHub Actions) |
| `gitlab` | GitLab (GitLab CI) |

---

## Esempi di Utilizzo

### In CI (automatico)

```bash
# GitHub Actions — tutto automatico
ai-review

# GitLab CI — tutto automatico
ai-review
```

### Manuale per GitHub

```bash
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITHUB_TOKEN=your_token

ai-review --provider github --repo owner/repo --pr 123
```

<small>
**Dove trovare i valori:**

- `--repo` — dall'URL del repository: `github.com/owner/repo` → `owner/repo`
- `--pr` — numero dall'URL: `github.com/owner/repo/pull/123` → `123`
</small>

### Manuale per GitLab

```bash
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITLAB_TOKEN=your_token

ai-review --provider gitlab --repo owner/repo --pr 456
```

<small>
**Dove trovare i valori:**

- `--repo` — percorso progetto dall'URL: `gitlab.com/group/project` → `group/project`
- `--pr` — numero MR dall'URL: `gitlab.com/group/project/-/merge_requests/456` → `456`
</small>

### Sintassi Breve

```bash
ai-review -p github -r owner/repo --pr 123
```

---

## Variabili d'Ambiente

CLI legge la configurazione dalle variabili d'ambiente:

### Necessarie

| Variabile | Descrizione |
|-----------|-------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Chiave API Gemini |
| `AI_REVIEWER_GITHUB_TOKEN` | Token GitHub (per GitHub) |
| `AI_REVIEWER_GITLAB_TOKEN` | Token GitLab (per GitLab) |

!!! tip "Fallback"
    I vecchi nomi senza prefisso (es. `GOOGLE_API_KEY`) funzionano ancora come fallback.

### Opzionali

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `AI_REVIEWER_LANGUAGE` | Lingua risposte | `en` |
| `AI_REVIEWER_LANGUAGE_MODE` | Modalità lingua | `adaptive` |
| `AI_REVIEWER_GEMINI_MODEL` | Modello Gemini | `gemini-2.5-flash` |
| `AI_REVIEWER_LOG_LEVEL` | Livello log | `INFO` |
| `AI_REVIEWER_GITLAB_URL` | URL GitLab | `https://gitlab.com` |

:point_right: [Lista completa →](configuration.md)

---

## Auto-rilevamento

### GitHub Actions

CLI usa automaticamente:

| Variabile | Descrizione |
|-----------|-------------|
| `GITHUB_ACTIONS` | Rilevamento ambiente |
| `GITHUB_REPOSITORY` | owner/repo |
| `GITHUB_EVENT_PATH` | JSON con dettagli PR |
| `GITHUB_REF` | Fallback per numero PR |

### GitLab CI

CLI usa automaticamente:

| Variabile | Descrizione |
|-----------|-------------|
| `GITLAB_CI` | Rilevamento ambiente |
| `CI_PROJECT_PATH` | owner/repo |
| `CI_MERGE_REQUEST_IID` | Numero MR |
| `CI_SERVER_URL` | URL GitLab |

---

## Codici di Uscita

| Codice | Descrizione |
|--------|-------------|
| `0` | Successo |
| `1` | Errore (configurazione, API, ecc.) |

---

## Logging

### Livelli

| Livello | Descrizione |
|---------|-------------|
| `DEBUG` | Informazioni dettagliate per debugging |
| `INFO` | Informazioni generali (default) |
| `WARNING` | Avvisi |
| `ERROR` | Errori |
| `CRITICAL` | Errori critici |

### Configurazione

```bash
export AI_REVIEWER_LOG_LEVEL=DEBUG
ai-review
```

### Output

CLI usa [Rich](https://rich.readthedocs.io/) per output formattato:

```
[12:34:56] INFO     Detected CI Provider: github
[12:34:56] INFO     Context extracted: owner/repo PR #123
[12:34:57] INFO     Fetching PR diff...
[12:34:58] INFO     Analyzing code with Gemini...
[12:35:02] INFO     Review completed successfully
```

---

## Errori

### Errore Configurazione

```
Configuration Error: AI_REVIEWER_GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Causa:** Configurazione non valida.

**Soluzione:** Controlla le variabili d'ambiente.

### Errore Contesto

```
Context Error: Could not determine PR number from GitHub Actions context.
```

**Causa:** Workflow non in esecuzione per PR.

**Soluzione:** Assicurati che il workflow abbia `on: pull_request`.

### Provider Non Rilevato

```
Error: Could not detect CI environment.
Please specify --provider, --repo, and --pr manually.
```

**Causa:** Esecuzione fuori dalla CI.

**Soluzione:** Specifica tutti i parametri manualmente.

---

## Comando Discover

Esegui il discovery del progetto standalone (senza creare una review):

```bash
ai-review discover <REPO> [OPTIONS]
```

### Argomenti

| Argomento | Descrizione |
|-----------|-------------|
| `REPO` | Repository (owner/repo) |

### Opzioni

| Opzione | Abbreviazione | Descrizione | Default |
|---------|---------------|-------------|---------|
| `--provider` | `-p` | Provider Git | `github` |
| `--json` | | Output in formato JSON | `false` |
| `--verbose` | `-v` | Mostra tutti i dettagli (convenzioni, strumenti CI, watch-files) | `false` |

### Esempi

```bash
# Repository GitHub
ai-review discover owner/repo

# Output JSON
ai-review discover owner/repo --json

# Modalità verbose
ai-review discover owner/repo -v

# Progetto GitLab
ai-review discover group/project -p gitlab
```

### Esempio di Output

```
🔍 Discovering project context...

Stack: Python (FastAPI) 3.13, uv
CI: ✅ .github/workflows/tests.yml — ruff, mypy, pytest

Attention Zones:
  ✅ Formatting — ruff format in CI
  ✅ Type checking — mypy --strict in CI
  ❌ Security scanning — No security scanner detected
  ⚠️ Test coverage — no coverage threshold
```

---

## Docker

Esegui via Docker:

```bash
docker run --rm \
  -e AI_REVIEWER_GOOGLE_API_KEY=your_key \
  -e AI_REVIEWER_GITHUB_TOKEN=your_token \
  ghcr.io/konstziv/ai-code-reviewer:1 \
  --provider github \
  --repo owner/repo \
  --pr 123
```

---

## Versione

```bash
ai-review --version
```

```
AI Code Reviewer 0.1.0
```

---

## Aiuto

```bash
ai-review --help
```

```
Usage: ai-review [OPTIONS]

  Run AI Code Reviewer.

  Automatically detects CI environment and reviews the current Pull Request.
  Can also be run manually by providing arguments.

Options:
  -p, --provider [github|gitlab]  CI provider (auto-detected if not provided)
  -r, --repo TEXT                 Repository name (e.g. owner/repo). Auto-detected in CI.
  --pr INTEGER                    Pull Request number. Auto-detected in CI.
  --help                          Show this message and exit.
```

---

## Prossimo Passo

- [Troubleshooting →](troubleshooting.md)
- [Esempi →](examples/index.md)
