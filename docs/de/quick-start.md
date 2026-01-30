# Schnellstart

Bringen Sie AI Code Reviewer in 1 Minute zum Laufen.

---

## GitHub Actions

### Schritt 1: Secret hinzufügen

`Settings → Secrets and variables → Actions → New repository secret`

| Name | Wert |
|------|------|
| `GOOGLE_API_KEY` | Ihr Gemini API-Schlüssel |

:point_right: [Schlüssel erhalten](https://aistudio.google.com/)

### Schritt 2: Workflow erstellen

Erstellen Sie im Stammverzeichnis Ihres Projekts die Datei `.github/workflows/ai-review.yml`

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
    # Nicht für Fork-PRs ausführen (kein Zugriff auf Secrets)
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

### Schritt 3: PR erstellen

Fertig! Das AI-Review erscheint automatisch.

---

## GitLab CI

### Schritt 1: Variable hinzufügen

`Settings → CI/CD → Variables`

| Name | Wert | Optionen |
|------|------|----------|
| `GOOGLE_API_KEY` | Ihr Gemini API-Schlüssel | Masked, Protected |

:point_right: [Schlüssel erhalten](https://aistudio.google.com/)

### Schritt 2: Job hinzufügen

Erstellen Sie im Stammverzeichnis Ihres Projekts die Datei `.gitlab-ci.yml`

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

!!! note "Für Inline-Kommentare"
    `CI_JOB_TOKEN` hat Einschränkungen. Für volle Funktionalität verwenden Sie [Personal Access Token](gitlab.md#personal-access-token).

### Schritt 3: MR erstellen

Fertig! Das AI-Review erscheint als Kommentare auf dem MR.

---

## Lokale Ausführung

Für lokales Testen benötigen Sie:

- **GOOGLE_API_KEY** — [bei Google AI Studio erhalten](https://aistudio.google.com/)
- **GITHUB_TOKEN** oder **GITLAB_TOKEN** — je nach Plattform:
    - GitHub: [PAT erhalten](github.md#get-token)
    - GitLab: [PAT erhalten](gitlab.md#get-token)

=== "GitHub"

    ```bash
    # Installieren
    pip install ai-reviewbot

    # Konfigurieren
    export GOOGLE_API_KEY=your_key
    export GITHUB_TOKEN=your_github_pat

    # Für GitHub PR ausführen
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab"

    ```bash
    # Installieren
    pip install ai-reviewbot

    # Konfigurieren
    export GOOGLE_API_KEY=your_key
    export GITLAB_TOKEN=your_gitlab_pat

    # Für GitLab MR ausführen
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

## Was kommt als Nächstes?

| Aufgabe | Dokument |
|---------|----------|
| Sprache konfigurieren | [Konfiguration](configuration.md) |
| Für GitHub optimieren | [GitHub-Leitfaden](github.md) |
| Für GitLab optimieren | [GitLab-Leitfaden](gitlab.md) |
| Beispiele ansehen | [Beispiele](examples/index.md) |

---

## Beispielergebnis

Nach der Ausführung sehen Sie Inline-Kommentare:

![AI Review Beispiel](https://via.placeholder.com/800x400?text=AI+Review+Inline+Comment)

Jeder Kommentar enthält:

- :red_circle: / :yellow_circle: / :blue_circle: Schweregrad-Badge
- Problembeschreibung
- **"Apply suggestion"**-Button
- Aufklappbare "Warum ist das wichtig?"-Erklärung

---

## Fehlerbehebung

### Review erscheint nicht?

1. Überprüfen Sie die CI-Job-Logs
2. Stellen Sie sicher, dass `GOOGLE_API_KEY` korrekt ist
3. Für GitHub: überprüfen Sie `permissions: pull-requests: write`
4. Für Fork-PRs: Secrets sind nicht verfügbar

### Rate Limit?

Gemini Free Tier: 15 RPM. Warten Sie eine Minute.

:point_right: [Alle Probleme →](troubleshooting.md)
