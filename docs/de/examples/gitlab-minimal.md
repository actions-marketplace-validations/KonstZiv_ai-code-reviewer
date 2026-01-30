# GitLab: Minimales Beispiel

Die einfachste Konfiguration für GitLab CI.

---

## Schritt 1: Variable hinzufügen

`Settings → CI/CD → Variables → Add variable`

| Name | Wert | Optionen |
|------|------|----------|
| `GOOGLE_API_KEY` | Ihr Gemini API-Schlüssel | Masked |

---

## Schritt 2: Job hinzufügen

`.gitlab-ci.yml`:

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

---

## Schritt 3: MR erstellen

Fertig! Das AI-Review erscheint als Kommentare auf dem MR.

---

## Was enthalten ist

| Funktion | Status |
|----------|--------|
| Notes auf MR | :white_check_mark: |
| Sprachadaptivität | :white_check_mark: (adaptive) |
| Metriken | :white_check_mark: |
| Auto-Retry | :white_check_mark: |

---

## Einschränkungen

| Einschränkung | Lösung |
|---------------|--------|
| MR bei Fehler blockiert | `allow_failure: true` hinzufügen |

---

## Nächster Schritt

:point_right: [Erweitertes Beispiel →](gitlab-advanced.md)
