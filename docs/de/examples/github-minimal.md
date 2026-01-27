# GitHub: Minimales Beispiel

Die einfachste Konfiguration für GitHub Actions.

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
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

---

## Schritt 3: PR erstellen

Fertig! Das AI-Review erscheint automatisch.

---

## Was enthalten ist

| Funktion | Status |
|----------|--------|
| Inline-Kommentare | :white_check_mark: |
| Apply Suggestion Button | :white_check_mark: |
| Sprachadaptivität | :white_check_mark: (adaptive) |
| Metriken | :white_check_mark: |

---

## Einschränkungen

| Einschränkung | Lösung |
|---------------|--------|
| Fork-PRs funktionieren nicht | Erwartetes Verhalten |
| Keine Concurrency | Siehe [erweitertes Beispiel](github-advanced.md) |
| Englisch standardmäßig | `language: uk` hinzufügen |

---

## Nächster Schritt

:point_right: [Erweitertes Beispiel →](github-advanced.md)
