# CLI-Referenz

AI Code Reviewer Befehlsreferenz.

---

## Hauptbefehl

```bash
ai-review [OPTIONS]
```

**Verhalten:**

- In CI (GitHub Actions / GitLab CI) — erkennt automatisch den Kontext
- Manuell — müssen `--provider`, `--repo`, `--pr` angeben

---

## Optionen

| Option | Kurz | Beschreibung | Standard |
|--------|------|--------------|----------|
| `--provider` | `-p` | CI-Provider | Auto-Erkennung |
| `--repo` | `-r` | Repository (owner/repo) | Auto-Erkennung |
| `--pr` | | PR/MR-Nummer | Auto-Erkennung |
| `--help` | | Hilfe anzeigen | |
| `--version` | | Version anzeigen | |

---

## Provider

| Wert | Beschreibung |
|------|--------------|
| `github` | GitHub (GitHub Actions) |
| `gitlab` | GitLab (GitLab CI) |

---

## Verwendungsbeispiele

### In CI (automatisch)

```bash
# GitHub Actions — alles automatisch
ai-review

# GitLab CI — alles automatisch
ai-review
```

### Manuell für GitHub

```bash
export GOOGLE_API_KEY=your_key
export GITHUB_TOKEN=your_token

ai-review --provider github --repo owner/repo --pr 123
```

<small>
**Wo die Werte erhalten:**

- `--repo` — aus Repository-URL: `github.com/owner/repo` → `owner/repo`
- `--pr` — Nummer aus URL: `github.com/owner/repo/pull/123` → `123`
</small>

### Manuell für GitLab

```bash
export GOOGLE_API_KEY=your_key
export GITLAB_TOKEN=your_token

ai-review --provider gitlab --repo owner/repo --pr 456
```

<small>
**Wo die Werte erhalten:**

- `--repo` — Projektpfad aus URL: `gitlab.com/group/project` → `group/project`
- `--pr` — MR-Nummer aus URL: `gitlab.com/group/project/-/merge_requests/456` → `456`
</small>

### Kurzsyntax

```bash
ai-review -p github -r owner/repo --pr 123
```

---

## Umgebungsvariablen

CLI liest Konfiguration aus Umgebungsvariablen:

### Erforderlich

| Variable | Beschreibung |
|----------|--------------|
| `GOOGLE_API_KEY` | Gemini API-Schlüssel |
| `GITHUB_TOKEN` | GitHub-Token (für GitHub) |
| `GITLAB_TOKEN` | GitLab-Token (für GitLab) |

### Optional

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `LANGUAGE` | Antwortsprache | `en` |
| `LANGUAGE_MODE` | Sprachmodus | `adaptive` |
| `GEMINI_MODEL` | Gemini-Modell | `gemini-2.5-flash` |
| `LOG_LEVEL` | Log-Level | `INFO` |
| `GITLAB_URL` | GitLab-URL | `https://gitlab.com` |

:point_right: [Vollständige Liste →](configuration.md)

---

## Auto-Erkennung

### GitHub Actions

CLI verwendet automatisch:

| Variable | Beschreibung |
|----------|--------------|
| `GITHUB_ACTIONS` | Umgebungserkennung |
| `GITHUB_REPOSITORY` | owner/repo |
| `GITHUB_EVENT_PATH` | JSON mit PR-Details |
| `GITHUB_REF` | Fallback für PR-Nummer |

### GitLab CI

CLI verwendet automatisch:

| Variable | Beschreibung |
|----------|--------------|
| `GITLAB_CI` | Umgebungserkennung |
| `CI_PROJECT_PATH` | owner/repo |
| `CI_MERGE_REQUEST_IID` | MR-Nummer |
| `CI_SERVER_URL` | GitLab-URL |

---

## Exit-Codes

| Code | Beschreibung |
|------|--------------|
| `0` | Erfolg |
| `1` | Fehler (Konfiguration, API, etc.) |

---

## Logging

### Level

| Level | Beschreibung |
|-------|--------------|
| `DEBUG` | Detaillierte Informationen für Debugging |
| `INFO` | Allgemeine Informationen (Standard) |
| `WARNING` | Warnungen |
| `ERROR` | Fehler |
| `CRITICAL` | Kritische Fehler |

### Konfiguration

```bash
export LOG_LEVEL=DEBUG
ai-review
```

### Ausgabe

CLI verwendet [Rich](https://rich.readthedocs.io/) für formatierte Ausgabe:

```
[12:34:56] INFO     Detected CI Provider: github
[12:34:56] INFO     Context extracted: owner/repo PR #123
[12:34:57] INFO     Fetching PR diff...
[12:34:58] INFO     Analyzing code with Gemini...
[12:35:02] INFO     Review completed successfully
```

---

## Fehler

### Konfigurationsfehler

```
Configuration Error: GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Ursache:** Ungültige Konfiguration.

**Lösung:** Überprüfen Sie die Umgebungsvariablen.

### Kontextfehler

```
Context Error: Could not determine PR number from GitHub Actions context.
```

**Ursache:** Workflow läuft nicht für PR.

**Lösung:** Stellen Sie sicher, dass der Workflow `on: pull_request` hat.

### Provider nicht erkannt

```
Error: Could not detect CI environment.
Please specify --provider, --repo, and --pr manually.
```

**Ursache:** Ausführung außerhalb von CI.

**Lösung:** Geben Sie alle Parameter manuell an.

---

## Docker

Ausführung über Docker:

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

## Version

```bash
ai-review --version
```

```
AI Code Reviewer 0.1.0
```

---

## Hilfe

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

## Nächster Schritt

- [Fehlerbehebung →](troubleshooting.md)
- [Beispiele →](examples/index.md)
