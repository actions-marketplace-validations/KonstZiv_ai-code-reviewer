# GitHub: Erweitertes Beispiel

Produktionsreife Konfiguration mit allen Best Practices.

---

## Schritt 1: Secret hinzufügen

`Settings → Secrets and variables → Actions → New repository secret`

| Name | Wert |
|------|------|
| `GOOGLE_API_KEY` | Ihr Gemini API-Schlüssel |

---

## Schritt 2: Datei erstellen

`.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
    # Optional: Dateifilter
    # paths:
    #   - '**.py'
    #   - '**.js'
    #   - '**.ts'

# Vorherige Ausführung bei neuem Commit abbrechen
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    name: AI Review
    runs-on: ubuntu-latest

    # Nicht für Fork-PRs ausführen (Secrets nicht verfügbar)
    if: github.event.pull_request.head.repo.full_name == github.repository

    # PR nicht blockieren, wenn Review fehlschlägt
    continue-on-error: true

    # Timeout-Schutz
    timeout-minutes: 10

    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Run AI Code Review
        uses: KonstZiv/ai-code-reviewer@v1
        with:
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
          language: uk
          language_mode: adaptive
          log_level: INFO
```

---

## Was enthalten ist

| Funktion | Status | Beschreibung |
|----------|--------|--------------|
| Inline-Kommentare | :white_check_mark: | Mit Apply Suggestion |
| Concurrency | :white_check_mark: | Bricht alte Läufe ab |
| Fork-Filter | :white_check_mark: | Überspringt Fork-PRs |
| Timeout | :white_check_mark: | Maximal 10 Minuten |
| Nicht-blockierend | :white_check_mark: | PR nicht blockiert |
| Benutzerdefinierte Sprache | :white_check_mark: | `language: uk` |

---

## Variationen

### Mit Dateifilter

```yaml
on:
  pull_request:
    paths:
      - 'src/**'
      - '**.py'
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Mit Branch-Filter

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

### Mit benutzerdefiniertem Modell

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    gemini_model: gemini-1.5-pro  # Leistungsstärkeres Modell
```

### Mit DEBUG-Logs

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    log_level: DEBUG
```

---

## Action-Optionen

| Input | Beschreibung | Standard |
|-------|--------------|----------|
| `google_api_key` | Gemini API-Schlüssel | **erforderlich** |
| `github_token` | GitHub-Token | `${{ github.token }}` |
| `language` | Antwortsprache | `en` |
| `language_mode` | `adaptive` / `fixed` | `adaptive` |
| `gemini_model` | Gemini-Modell | `gemini-2.0-flash` |
| `log_level` | Log-Level | `INFO` |

---

## Fehlerbehebung

### Review erscheint nicht

1. Workflow-Logs überprüfen
2. Überprüfen, ob es kein Fork-PR ist
3. `permissions: pull-requests: write` überprüfen

### Rate Limit

Concurrency bricht automatisch alte Läufe ab und reduziert die Last.

---

## Nächster Schritt

:point_right: [GitLab-Beispiele →](gitlab-minimal.md)
