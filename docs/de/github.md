# GitHub

Detaillierter Leitfaden für die Integration mit GitHub Actions.

---

## Berechtigungen

### Mindestberechtigungen

```yaml
permissions:
  contents: read        # Code lesen
  pull-requests: write  # Kommentare posten
```

### GITHUB_TOKEN in Actions

In GitHub Actions ist `GITHUB_TOKEN` automatisch verfügbar:

```yaml
env:
  GITHUB_TOKEN: ${{ github.token }}
```

**Automatische Token-Berechtigungen:**

| Berechtigung | Status | Hinweis |
|--------------|--------|---------|
| `contents: read` | :white_check_mark: | Standard |
| `pull-requests: write` | :white_check_mark: | Muss in `permissions` angegeben werden |

!!! warning "Fork-PRs"
    Für PRs aus Fork-Repositories hat `GITHUB_TOKEN` **nur Leseberechtigungen**.

    AI Review kann keine Kommentare für Fork-PRs posten.

### Personal Access Token erhalten {#get-token}

Für **lokale Ausführungen** benötigen Sie einen Personal Access Token (PAT):

1. Gehen Sie zu `Settings → Developer settings → Personal access tokens`
2. Wählen Sie **Fine-grained tokens** (empfohlen) oder Classic
3. Klicken Sie auf **Generate new token**

**Fine-grained Token (empfohlen):**

| Einstellung | Wert |
|-------------|------|
| Repository access | Only select repositories → Ihr Repository |
| Permissions | `Pull requests: Read and write` |

**Classic Token:**

| Scope | Beschreibung |
|-------|--------------|
| `repo` | Voller Zugriff auf Repository |

4. Klicken Sie auf **Generate token**
5. Kopieren Sie den Token und speichern Sie ihn als `GITHUB_TOKEN`

!!! warning "Token speichern"
    GitHub zeigt den Token **nur einmal** an. Speichern Sie ihn sofort.

---

## Trigger

### Empfohlener Trigger

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

| Typ | Wann ausgelöst |
|-----|----------------|
| `opened` | PR erstellt |
| `synchronize` | Neue Commits im PR |
| `reopened` | PR wieder geöffnet |

### Dateifilterung

Review nur für bestimmte Dateien ausführen:

```yaml
on:
  pull_request:
    paths:
      - '**.py'
      - '**.js'
      - '**.ts'
```

### Branch-Filterung

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

---

## Secrets

### Secrets hinzufügen

`Settings → Secrets and variables → Actions → New repository secret`

| Secret | Erforderlich | Beschreibung |
|--------|--------------|--------------|
| `GOOGLE_API_KEY` | :white_check_mark: | Gemini API-Schlüssel |

### Verwendung

```yaml
env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

!!! danger "Secrets niemals hartcodieren"
    ```yaml
    # ❌ FALSCH
    env:
      GOOGLE_API_KEY: AIza...

    # ✅ RICHTIG
    env:
      GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
    ```

---

## Workflow-Beispiele

### Minimal

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

!!! info "Über `GITHUB_TOKEN`"
    `secrets.GITHUB_TOKEN` ist ein **automatisches Token**, das GitHub für jeden Workflow-Lauf erstellt. Sie müssen es **nicht** manuell zu den Secrets hinzufügen — es ist bereits verfügbar.

    Token-Berechtigungen werden durch den `permissions`-Abschnitt in der Workflow-Datei definiert.

    :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

### Mit Concurrency (empfohlen)

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
    if: github.event.pull_request.head.repo.full_name == github.repository
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
          language: uk
          language_mode: adaptive
```

**Was Concurrency bewirkt:**

- Wenn ein neuer Commit gepusht wird, während das Review noch läuft — wird das alte Review abgebrochen
- Spart Ressourcen und API-Aufrufe

### Mit Fork-PR-Filterung

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    # Nicht für Fork-PRs ausführen (kein Zugriff auf Secrets)
    if: github.event.pull_request.head.repo.full_name == github.repository
```

---

## GitHub Action Inputs

| Input | Beschreibung | Standard |
|-------|--------------|----------|
| `google_api_key` | Gemini API-Schlüssel | **erforderlich** |
| `github_token` | GitHub-Token | `${{ github.token }}` |
| `language` | Antwortsprache | `en` |
| `language_mode` | Sprachmodus | `adaptive` |
| `gemini_model` | Gemini-Modell | `gemini-2.5-flash` |
| `log_level` | Log-Level | `INFO` |
| `review_max_comment_chars` | Max. MR-Kommentarzeichen im Prompt | `3000` |
| `review_include_bot_comments` | Bot-Kommentare in Prompt einbeziehen | `true` |
| `review_post_inline_comments` | Inline-Kommentare an Codezeilen posten | `true` |
| `gemini_model_fallback` | Fallback-Modell bei Kontingenterschöpfung | `gemini-3-flash-preview` |
| `review_enable_dialogue` | Kommentare in Dialoge gruppieren | `true` |
| `discovery_enabled` | Project Discovery aktivieren | `true` |
| `discovery_verbose` | Discovery-Kommentar immer posten | `false` |
| `discovery_timeout` | Discovery-Timeout in Sekunden | `30` |

!!! tip "Umgebungsvariablen"
    Die Action ordnet Inputs intern `AI_REVIEWER_*`-Umgebungsvariablen zu. Beim Ausführen außerhalb der Action verwenden Sie `AI_REVIEWER_*`-Variablen direkt (alte Namen wie `GOOGLE_API_KEY` funktionieren weiterhin als Fallback).

---

## Review-Ergebnis

### Inline-Kommentare

AI Review postet Kommentare direkt an Code-Zeilen:

- :red_circle: **CRITICAL** — kritische Probleme (Sicherheit, Bugs)
- :yellow_circle: **WARNING** — Empfehlungen
- :blue_circle: **INFO** — lehrreiche Hinweise

### Apply Suggestion

Jeder Kommentar mit einem Code-Vorschlag hat einen **"Apply suggestion"**-Button:

```suggestion
fixed_code_here
```

GitHub rendert dies automatisch als interaktiven Button.

### Zusammenfassung

Am Ende des Reviews wird eine Zusammenfassung gepostet mit:

- Gesamtstatistik der Probleme
- Metriken (Zeit, Tokens, Kosten)
- Gute Praktiken (positives Feedback)

---

## Fehlerbehebung

### Review postet keine Kommentare

**Überprüfen:**

1. `permissions: pull-requests: write` ist im Workflow
2. `GOOGLE_API_KEY`-Secret ist gesetzt
3. PR ist nicht aus einem Fork-Repository

### "Resource not accessible by integration"

**Ursache:** Unzureichende Berechtigungen.

**Lösung:** Berechtigungen hinzufügen:

```yaml
permissions:
  contents: read
  pull-requests: write
```

### Rate Limit von Gemini

**Ursache:** Free-Tier-Limit überschritten (15 RPM).

**Lösung:**

- Eine Minute warten
- `concurrency` hinzufügen, um alte Läufe abzubrechen
- Kostenpflichtiges Tier in Betracht ziehen

---

## Best Practices

### 1. Immer Concurrency verwenden

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

### 2. Fork-PRs filtern

```yaml
if: github.event.pull_request.head.repo.full_name == github.repository
```

### 3. Timeout setzen

```yaml
jobs:
  review:
    timeout-minutes: 10
```

### 4. Job nicht-blockierend machen

```yaml
jobs:
  review:
    continue-on-error: true
```

---

## Nächster Schritt

- [GitLab-Integration →](gitlab.md)
- [CLI-Referenz →](api.md)
