# Installation

Die Installationsoption hängt von Ihrem Anwendungsfall und Ihren Zielen ab.

---

## 1. CI/CD — Automatisiertes Review {#ci-cd}

Das häufigste Szenario: AI Code Reviewer läuft automatisch, wenn ein PR/MR erstellt oder aktualisiert wird.

Einrichtung in 5 Minuten:

- :octicons-mark-github-16: **[Review für GitHub einrichten →](quick-start.md)**

    :point_right: [Workflow-Beispiele →](examples/github-minimal.md) · [Detaillierter GitHub-Leitfaden →](github.md)

- :simple-gitlab: **[Review für GitLab einrichten →](quick-start.md)**

    :point_right: [Workflow-Beispiele →](examples/gitlab-minimal.md) · [Detaillierter GitLab-Leitfaden →](gitlab.md)

Für Feinabstimmung siehe [Konfiguration →](configuration.md)

---

## 2. Eigenständige Bereitstellung: CLI/Docker {#standalone}

CLI und Docker-Image ermöglichen die Ausführung von AI Code Reviewer außerhalb der Standard-CI-Pipeline.

### Anwendungsfälle

| Szenario | Wie umsetzen |
|----------|--------------|
| **Manueller Start** | Lokales Terminal — Debugging, Demo, Evaluierung |
| **Scheduled Review** | GitLab Scheduled Pipeline / GitHub Actions `schedule` / cron |
| **Batch Review** | Skript, das über offene PR/MR iteriert |
| **Eigener Server** | Docker auf Server mit Zugriff auf Git API |
| **On-demand Review** | Webhook → Container-Start |

### Erforderliche Umgebungsvariablen

| Variable | Beschreibung | Wann benötigt | Wie erhalten |
|----------|--------------|---------------|--------------|
| `GOOGLE_API_KEY` | Gemini API-Schlüssel | **Immer** | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Für GitHub | [Anleitung](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab Personal Access Token | Für GitLab | [Anleitung](gitlab.md#get-token) |

---

### Manueller Start

Für Debugging, Demo, Evaluierung vor dem Deployment, retrospektive PR/MR-Analyse.

#### Docker (empfohlen)

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

#### pip / uv

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

### Scheduled Reviews

Review nach Zeitplan ausführen — zur Ressourceneinsparung oder wenn sofortiges Feedback nicht erforderlich ist.

=== "GitLab Scheduled Pipeline"

    ```yaml
    # .gitlab-ci.yml
    ai-review-scheduled:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      script:
        - |
          # Liste der offenen MR abrufen
          MR_LIST=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
            "$CI_SERVER_URL/api/v4/projects/$CI_PROJECT_ID/merge_requests?state=opened" \
            | jq -r '.[].iid')

          # Review für jeden MR ausführen
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

    **Zeitplan einrichten:** Project → Build → Pipeline schedules → New schedule

=== "GitHub Actions Schedule"

    ```yaml
    # .github/workflows/scheduled-review.yml
    name: Scheduled AI Review

    on:
      schedule:
        - cron: '0 9 * * *'  # Täglich um 9:00 UTC

    jobs:
      review-open-prs:
        runs-on: ubuntu-latest
        steps:
          - name: Get open PRs and review
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
            run: |
              # Liste der offenen PR abrufen
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

### Eigener Server / private Umgebung

Für die Bereitstellung auf eigener Infrastruktur mit Zugriff auf Git API.

**Optionen:**

- **Docker auf Server** — Ausführung über cron, systemd timer oder als Service
- **Kubernetes** — CronJob für Scheduled Reviews
- **Self-hosted GitLab** — Variable `GITLAB_URL` hinzufügen (siehe Beispiel unten)

**Beispiel cron job:**

```bash
# /etc/cron.d/ai-review
# Täglich um 10:00 Review für alle offenen MR ausführen
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
    Für Self-hosted GitLab fügen Sie die Variable `GITLAB_URL` hinzu:

    ```bash
    -e GITLAB_URL=https://gitlab.company.com
    ```

---

## 3. Contributors / Entwicklung {#development}

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
