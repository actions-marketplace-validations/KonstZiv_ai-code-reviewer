# GitLab: Esempio Minimo

La configurazione piu semplice per GitLab CI.

---

## Passo 1: Aggiungi una Variabile

`Settings → CI/CD → Variables → Add variable`

| Nome | Valore | Opzioni |
|------|--------|---------|
| `GOOGLE_API_KEY` | La tua chiave API Gemini | Masked |

---

## Passo 2: Aggiungi un Job

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

## Passo 3: Crea una MR

Fatto! La revisione AI apparira come commenti sulla MR.

---

## Cosa Include

| Funzionalita | Stato |
|--------------|-------|
| Note sulla MR | :white_check_mark: |
| Adattivita linguistica | :white_check_mark: (adaptive) |
| Metriche | :white_check_mark: |
| Auto-retry | :white_check_mark: |

---

## Limitazioni

| Limitazione | Soluzione |
|-------------|-----------|
| MR bloccata in caso di errore | Aggiungi `allow_failure: true` |

---

## Prossimo Passo

:point_right: [Esempio avanzato →](gitlab-advanced.md)
