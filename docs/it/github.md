# GitHub

Guida dettagliata per l'integrazione con GitHub Actions.

---

## Permessi

### Permessi Minimi

```yaml
permissions:
  contents: read        # Leggi codice
  pull-requests: write  # Pubblica commenti
```

### GITHUB_TOKEN in Actions

In GitHub Actions, `GITHUB_TOKEN` e automaticamente disponibile:

```yaml
env:
  GITHUB_TOKEN: ${{ github.token }}
```

**Permessi automatici del token:**

| Permesso | Stato | Nota |
|----------|-------|------|
| `contents: read` | :white_check_mark: | Default |
| `pull-requests: write` | :white_check_mark: | Deve essere specificato in `permissions` |

!!! warning "PR da Fork"
    Per PR da repository fork, `GITHUB_TOKEN` ha permessi **solo lettura**.

    AI Review non puo pubblicare commenti per PR da fork.

### Come Ottenere un Personal Access Token {#get-token}

Per **esecuzioni locali**, hai bisogno di un Personal Access Token (PAT):

1. Vai su `Settings → Developer settings → Personal access tokens`
2. Scegli **Fine-grained tokens** (consigliato) o Classic
3. Clicca **Generate new token**

**Fine-grained token (consigliato):**

| Impostazione | Valore |
|--------------|--------|
| Repository access | Only select repositories → il tuo repository |
| Permissions | `Pull requests: Read and write` |

**Classic token:**

| Scope | Descrizione |
|-------|-------------|
| `repo` | Accesso completo al repository |

4. Clicca **Generate token**
5. Copia il token e salvalo come `GITHUB_TOKEN`

!!! warning "Salva il token"
    GitHub mostra il token **una sola volta**. Salvalo immediatamente.

---

## Trigger

### Trigger Consigliato

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

| Tipo | Quando si attiva |
|------|------------------|
| `opened` | PR creato |
| `synchronize` | Nuovi commit nel PR |
| `reopened` | PR riaperto |

### Filtro File

Esegui la revisione solo per file specifici:

```yaml
on:
  pull_request:
    paths:
      - '**.py'
      - '**.js'
      - '**.ts'
```

### Filtro Branch

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

---

## Secret

### Aggiungere Secret

`Settings → Secrets and variables → Actions → New repository secret`

| Secret | Necessario | Descrizione |
|--------|------------|-------------|
| `GOOGLE_API_KEY` | :white_check_mark: | Chiave API Gemini |

### Utilizzo

```yaml
env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

!!! danger "Mai hardcodare i secret"
    ```yaml
    # ❌ SBAGLIATO
    env:
      GOOGLE_API_KEY: AIza...

    # ✅ CORRETTO
    env:
      GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
    ```

---

## Esempi Workflow

### Minimo

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

!!! info "Informazioni su `GITHUB_TOKEN`"
    `secrets.GITHUB_TOKEN` e un **token automatico** che GitHub crea per ogni esecuzione del workflow. **Non e necessario** aggiungerlo manualmente ai secret — e gia disponibile.

    I permessi del token sono definiti dalla sezione `permissions` nel file workflow.

    :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

### Con Concurrency (consigliato)

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

**Cosa fa la concurrency:**

- Se un nuovo commit viene pushato mentre la revisione e ancora in esecuzione — la vecchia revisione viene cancellata
- Risparmia risorse e chiamate API

### Con Filtro PR da Fork

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    # Non eseguire per PR da fork (nessun accesso ai secret)
    if: github.event.pull_request.head.repo.full_name == github.repository
```

---

## Input della GitHub Action

| Input | Descrizione | Default |
|-------|-------------|---------|
| `google_api_key` | Chiave API Gemini | **necessario** |
| `github_token` | Token GitHub | `${{ github.token }}` |
| `language` | Lingua risposte | `en` |
| `language_mode` | Modalita lingua | `adaptive` |
| `gemini_model` | Modello Gemini | `gemini-2.0-flash` |
| `log_level` | Livello log | `INFO` |

---

## Risultato della Review

### Commenti Inline

AI Review pubblica commenti direttamente sulle righe di codice:

- :red_circle: **CRITICAL** — problemi critici (sicurezza, bug)
- :yellow_circle: **WARNING** — raccomandazioni
- :blue_circle: **INFO** — note educative

### Apply Suggestion

Ogni commento con un suggerimento di codice ha un pulsante **"Apply suggestion"**:

```suggestion
fixed_code_here
```

GitHub lo renderizza automaticamente come pulsante interattivo.

### Summary

Alla fine della revisione, viene pubblicato un Summary con:

- Statistiche generali dei problemi
- Metriche (tempo, token, costo)
- Good practice (feedback positivo)

---

## Troubleshooting

### La Review Non Pubblica Commenti

**Controlla:**

1. `permissions: pull-requests: write` e nel workflow
2. Il secret `GOOGLE_API_KEY` e impostato
3. Il PR non e da un repository fork

### "Resource not accessible by integration"

**Causa:** Permessi insufficienti.

**Soluzione:** Aggiungi i permessi:

```yaml
permissions:
  contents: read
  pull-requests: write
```

### Rate Limit da Gemini

**Causa:** Limite free tier superato (15 RPM).

**Soluzione:**

- Aspetta un minuto
- Aggiungi `concurrency` per cancellare le vecchie esecuzioni
- Considera il tier a pagamento

---

## Best Practice

### 1. Usa sempre concurrency

```yaml
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

### 2. Filtra PR da fork

```yaml
if: github.event.pull_request.head.repo.full_name == github.repository
```

### 3. Imposta timeout

```yaml
jobs:
  review:
    timeout-minutes: 10
```

### 4. Rendi il job non bloccante

```yaml
jobs:
  review:
    continue-on-error: true
```

---

## Prossimo Passo

- [Integrazione GitLab →](gitlab.md)
- [Riferimento CLI →](api.md)
