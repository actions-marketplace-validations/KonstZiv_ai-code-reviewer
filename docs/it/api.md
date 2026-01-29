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
export GOOGLE_API_KEY=your_key
export GITHUB_TOKEN=your_token

ai-review --provider github --repo owner/repo --pr 123
```

<small>
**Dove trovare i valori:**

- `--repo` — dall'URL del repository: `github.com/owner/repo` → `owner/repo`
- `--pr` — numero dall'URL: `github.com/owner/repo/pull/123` → `123`
</small>

### Manuale per GitLab

```bash
export GOOGLE_API_KEY=your_key
export GITLAB_TOKEN=your_token

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
| `GOOGLE_API_KEY` | Chiave API Gemini |
| `GITHUB_TOKEN` | Token GitHub (per GitHub) |
| `GITLAB_TOKEN` | Token GitLab (per GitLab) |

### Opzionali

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `LANGUAGE` | Lingua risposte | `en` |
| `LANGUAGE_MODE` | Modalita lingua | `adaptive` |
| `GEMINI_MODEL` | Modello Gemini | `gemini-2.5-flash` |
| `LOG_LEVEL` | Livello log | `INFO` |
| `GITLAB_URL` | URL GitLab | `https://gitlab.com` |

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
export LOG_LEVEL=DEBUG
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
Configuration Error: GOOGLE_API_KEY is too short (minimum 10 characters)
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

## Docker

Esegui via Docker:

```bash
docker run --rm \
  -e GOOGLE_API_KEY=your_key \
  -e GITHUB_TOKEN=your_token \
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
