# Installation

Die Installationsoption hängt von Ihrem Anwendungsfall und Ihren Zielen ab.

---

## 1. CI/CD — Automatisiertes Review {#ci-cd}

Das häufigste Szenario: AI Code Reviewer läuft automatisch, wenn ein PR/MR erstellt oder aktualisiert wird.

### GitHub Actions

Der einfachste Weg für GitHub — verwenden Sie die fertige GitHub Action:

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

**Erforderliche Einrichtung:**

| Was benötigt wird | Wo konfigurieren |
|-------------------|------------------|
| `GOOGLE_API_KEY` | Repository → Settings → Secrets → Actions |

:point_right: [Vollständiges Beispiel mit Concurrency und Filterung →](quick-start.md#github-actions)

:point_right: [Detaillierter GitHub-Leitfaden →](github.md)

---

### GitLab CI

Für GitLab verwenden Sie das Docker-Image in `.gitlab-ci.yml`:

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

**Erforderliche Einrichtung:**

| Was benötigt wird | Wo konfigurieren |
|-------------------|------------------|
| `GOOGLE_API_KEY` | Project → Settings → CI/CD → Variables (Masked) |
| `GITLAB_TOKEN` | Optional, für Inline-Kommentare ([Details](gitlab.md#tokens)) |

:point_right: [Vollständiges Beispiel →](quick-start.md#gitlab-ci)

:point_right: [Detaillierter GitLab-Leitfaden →](gitlab.md)

---

## 2. Lokales Testen / Evaluierung {#local}

### Warum wird das benötigt?

1. **Evaluierung vor dem Deployment** — testen Sie an einem echten PR, bevor Sie es zu CI hinzufügen
2. **Debugging** — wenn etwas in CI nicht funktioniert, führen Sie es lokal mit `--log-level DEBUG` aus
3. **Retrospektives Review** — analysieren Sie einen alten PR/MR
4. **Demo** — zeigen Sie dem Team/Management, wie es funktioniert

### Wie es funktioniert

```
Lokales Terminal
       │
       ▼
   ai-review CLI
       │
       ├──► GitHub/GitLab API (liest PR/MR, Diff, verknüpfte Issues)
       │
       ├──► Gemini API (erhält Review)
       │
       └──► GitHub/GitLab API (veröffentlicht Kommentare)
```

### Erforderliche Umgebungsvariablen

| Variable | Beschreibung | Wann benötigt | Wie erhalten |
|----------|--------------|---------------|--------------|
| `GOOGLE_API_KEY` | Gemini API-Schlüssel | **Immer** | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Für GitHub | [Anleitung](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab Personal Access Token | Für GitLab | [Anleitung](gitlab.md#get-token) |

---

### Option A: Docker (empfohlen)

Keine Python-Installation erforderlich — alles ist im Container enthalten.

**Schritt 1: Image herunterladen**

```bash
docker pull ghcr.io/konstziv/ai-code-reviewer:1
```

**Schritt 2: Review ausführen**

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

!!! tip "Docker-Images"
    Verfügbar von zwei Registries:

    - `ghcr.io/konstziv/ai-code-reviewer:1` — GitHub Container Registry
    - `koszivdocker/ai-reviewbot:1` — DockerHub

---

### Option B: pip / uv

Installation als Python-Paket.

**Schritt 1: Installieren**

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

!!! note "Python-Version"
    Erfordert Python **3.13+**

**Schritt 2: Variablen einrichten**

```bash
export GOOGLE_API_KEY=your_api_key
export GITHUB_TOKEN=your_token  # oder GITLAB_TOKEN für GitLab
```

**Schritt 3: Ausführen**

=== "GitHub PR"

    ```bash
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab MR"

    ```bash
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

### Optionale Variablen

Zusätzliche Variablen sind für die Feinabstimmung verfügbar:

| Variable | Standard | Wirkung |
|----------|----------|---------|
| `LANGUAGE` | `en` | Antwortsprache (ISO 639) |
| `LANGUAGE_MODE` | `adaptive` | Spracherkennungsmodus |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini-Modell |
| `LOG_LEVEL` | `INFO` | Logging-Level |

:point_right: [Vollständige Liste der Variablen →](configuration.md#optional)

---

## 3. Unternehmensumgebung (air-gapped) {#airgapped}

Für Umgebungen mit eingeschränktem Internetzugang.

### Einschränkungen

!!! warning "Gemini API-Zugriff erforderlich"
    AI Code Reviewer verwendet die Google Gemini API für Code-Analyse.

    **Erforderlicher Zugriff auf:** `generativelanguage.googleapis.com`

    Unterstützung für lokal bereitgestellte LLM-Modelle ist **noch nicht implementiert**.

### Docker-Image-Bereitstellung

**Schritt 1: Auf einer Maschine mit Internetzugang**

```bash
# Image herunterladen
docker pull ghcr.io/konstziv/ai-code-reviewer:1

# In Datei speichern
docker save ghcr.io/konstziv/ai-code-reviewer:1 > ai-code-reviewer.tar
```

**Schritt 2: Datei in die geschlossene Umgebung übertragen**

**Schritt 3: In interne Registry laden**

```bash
# Aus Datei laden
docker load < ai-code-reviewer.tar

# Für interne Registry neu taggen
docker tag ghcr.io/konstziv/ai-code-reviewer:1 \
    registry.internal.company.com/devops/ai-code-reviewer:1

# Pushen
docker push registry.internal.company.com/devops/ai-code-reviewer:1
```

**Schritt 4: In GitLab CI verwenden**

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

## 4. Contributors / Entwicklung {#development}

Wenn Sie Zeit und Inspiration haben, bei der Entwicklung des Pakets zu helfen, oder es als Grundlage für Ihre eigene Entwicklung verwenden möchten — wir begrüßen und ermutigen solche Aktionen aufrichtig!

### Entwicklungsinstallation

```bash
# Repository klonen
git clone https://github.com/KonstZiv/ai-code-reviewer.git
cd ai-code-reviewer

# Abhängigkeiten installieren (wir verwenden uv)
uv sync

# Überprüfen
uv run ai-review --help

# Tests ausführen
uv run pytest

# Qualitätsprüfungen ausführen
uv run ruff check .
uv run mypy .
```

!!! info "uv"
    Wir verwenden [uv](https://github.com/astral-sh/uv) für das Dependency-Management.

    Installation: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Projektstruktur

```
ai-code-reviewer/
├── src/ai_reviewer/      # Quellcode
│   ├── core/             # Models, Config, Formatierung
│   ├── integrations/     # GitHub, GitLab, Gemini
│   └── utils/            # Utilities
├── tests/                # Tests
├── docs/                 # Dokumentation
└── examples/             # CI-Konfigurationsbeispiele
```

:point_right: [Wie Sie beitragen können →](https://github.com/KonstZiv/ai-code-reviewer/blob/main/CONTRIBUTING.md)

---

## Anforderungen {#requirements}

### Systemanforderungen

| Komponente | Anforderung |
|------------|-------------|
| Python | 3.13+ (für pip-Installation) |
| Docker | 20.10+ (für Docker) |
| OS | Linux, macOS, Windows |
| RAM | 256MB+ |
| Netzwerk | Zugriff auf `generativelanguage.googleapis.com` |

### API-Schlüssel

| Schlüssel | Erforderlich | Wie erhalten |
|-----------|--------------|--------------|
| Google Gemini API | **Ja** | [Google AI Studio](https://aistudio.google.com/) |
| GitHub PAT | Für GitHub | [Anleitung](github.md#get-token) |
| GitLab PAT | Für GitLab | [Anleitung](gitlab.md#get-token) |

### Gemini API-Limits

!!! info "Free Tier"
    Google Gemini hat einen Free Tier:

    | Limit | Wert |
    |-------|------|
    | Anfragen pro Minute | 15 RPM |
    | Tokens pro Tag | 1M |
    | Anfragen pro Tag | 1500 |

    Dies ist für die meisten Projekte ausreichend.

---

## Nächster Schritt

:point_right: [Schnellstart →](quick-start.md)
