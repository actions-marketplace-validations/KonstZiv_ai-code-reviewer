# GitLab

Guida dettagliata per l'integrazione con GitLab CI.

---

## Token {#tokens}

### CI_JOB_TOKEN (automatico)

In GitLab CI, `CI_JOB_TOKEN` e automaticamente disponibile:

```yaml
variables:
  AI_REVIEWER_GITLAB_TOKEN: $CI_JOB_TOKEN
```

**Limitazioni di `CI_JOB_TOKEN`:**

| Funzionalita | Stato |
|--------------|-------|
| Leggi MR | :white_check_mark: |
| Leggi diff | :white_check_mark: |
| Pubblica note | :white_check_mark: |
| Crea discussioni | :x: |

!!! warning "Permessi limitati"
    `CI_JOB_TOKEN` non puo creare discussioni inline.

    Per la funzionalita completa, usa un Personal Access Token.

### Personal Access Token (PAT) {#get-token}

Per **tutti i piani GitLab** (incluso Free). Consigliato per esecuzioni locali o funzionalita completa in CI.

**Come creare:**

1. Vai su **User Settings → Access Tokens → Add new token**
    - URL: `https://gitlab.com/-/user_settings/personal_access_tokens`
2. Compila i campi:
    - **Token name:** `ai-code-reviewer`
    - **Expiration date:** imposta secondo necessita (es. 1 anno)
    - **Scopes:** seleziona **`api`**
3. Clicca **Create personal access token**
4. **Copia il token immediatamente** — GitLab lo mostra una sola volta!

**Come usare in CI:**

1. Vai su **Settings → CI/CD → Variables → Add variable**
2. Aggiungi la variabile:
    - **Key:** `AI_REVIEWER_GITLAB_TOKEN` (o `GITLAB_TOKEN`)
    - **Value:** incolla il tuo token
    - **Flags:** seleziona **Masked** e **Protected**
3. Usa in `.gitlab-ci.yml`:

```yaml
variables:
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_TOKEN  # Personal Access Token da CI/CD Variables
```

!!! warning "Salva il token"
    GitLab mostra il token **una sola volta**. Salvalo immediatamente in un luogo sicuro.

### Project Access Token (:material-crown: Premium/Ultimate) {#project-token}

Disponibile solo sui piani **GitLab Premium** e **Ultimate**. Una buona scelta se preferisci un token con ambito di progetto invece di uno personale.

**Vantaggi rispetto al PAT:**

- Limitato a un singolo progetto (nessun accesso ad altri progetti)
- Puo essere revocato dai maintainer del progetto (nessuna dipendenza da un utente specifico)
- Migliore per i team — non legato a un account personale

**Come creare:**

1. Vai su **Project → Settings → Access Tokens**
    - URL: `https://gitlab.com/<owner>/<repo>/-/settings/access_tokens`
2. Compila i campi:
    - **Token name:** `ai-code-reviewer`
    - **Role:** `Developer` (minimo richiesto)
    - **Scopes:** seleziona **`api`**
3. Clicca **Create project access token**
4. **Copia il token immediatamente**

**Come usare in CI:**

Come il PAT — aggiungi come `AI_REVIEWER_GITLAB_TOKEN` nelle CI/CD Variables:

```yaml
variables:
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_PROJECT_TOKEN  # Project Access Token da CI/CD Variables
```

!!! info "Quale token scegliere?"
    | | CI_JOB_TOKEN | Personal Access Token | Project Access Token |
    |---|---|---|---|
    | **Piano** | Tutti | Tutti (incluso Free) | Solo Premium/Ultimate |
    | **Configurazione** | Automatica | Manuale | Manuale |
    | **Ambito** | Solo il job corrente | Tutti i progetti dell'utente | Singolo progetto |
    | **Commenti inline** | :x: | :white_check_mark: | :white_check_mark: |
    | **Ideale per** | Avvio rapido | Piano Free + funzionalita completa | Team su Premium/Ultimate |

---

## Variabili CI/CD

### Aggiungere Variabili

`Settings → CI/CD → Variables → Add variable`

| Variabile | Valore | Opzioni |
|-----------|--------|---------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Chiave API Gemini | Masked |
| `AI_REVIEWER_GITLAB_TOKEN` | PAT (se necessario) | Masked |

!!! tip "Masked"
    Abilita sempre **Masked** per i secret — non verranno mostrati nei log.

---

## Trigger

### Trigger Consigliato

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Questo esegue il job solo per le pipeline di Merge Request.

### Trigger Alternativo (only/except)

```yaml
only:
  - merge_requests
```

!!! note "rules vs only"
    `rules` — sintassi piu recente, consigliata da GitLab.

---

## Esempi Job

### Minimo

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    AI_REVIEWER_GOOGLE_API_KEY: $GOOGLE_API_KEY
    AI_REVIEWER_GITLAB_TOKEN: $CI_JOB_TOKEN  # Automatico, nessuna configurazione necessaria
```

### Completo (consigliato)

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  timeout: 10m
  variables:
    AI_REVIEWER_GOOGLE_API_KEY: $GOOGLE_API_KEY
    # CI_JOB_TOKEN (automatico) o Personal Access Token per permessi completi:
    AI_REVIEWER_GITLAB_TOKEN: $CI_JOB_TOKEN    # o: $GITLAB_PAT (vedi "Ottenere il token")
    AI_REVIEWER_LANGUAGE: uk
    AI_REVIEWER_LANGUAGE_MODE: adaptive
  interruptible: true
```

**Cosa fa:**

- `allow_failure: true` — la MR non viene bloccata se la revisione fallisce
- `timeout: 10m` — massimo 10 minuti
- `interruptible: true` — puo essere cancellato con un nuovo commit

### Con Stage Personalizzato

```yaml
stages:
  - test
  - review
  - deploy

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  needs: []  # Non aspettare gli stage precedenti
```

---

## GitLab Self-hosted

### Configurazione

```yaml
variables:
  AI_REVIEWER_GITLAB_URL: https://gitlab.mycompany.com
  AI_REVIEWER_GOOGLE_API_KEY: $GOOGLE_API_KEY
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_TOKEN
```

### Docker Registry

Se il tuo GitLab non ha accesso a `ghcr.io`, crea un mirror:

```bash
# Su una macchina con accesso
docker pull ghcr.io/konstziv/ai-code-reviewer:1
docker tag ghcr.io/konstziv/ai-code-reviewer:1 \
    gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
docker push gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
```

```yaml
ai-review:
  image: gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
```

---

## Variabili CI GitLab

AI Code Reviewer usa automaticamente:

| Variabile | Descrizione |
|-----------|-------------|
| `CI_PROJECT_PATH` | `owner/repo` |
| `CI_MERGE_REQUEST_IID` | Numero MR |
| `CI_SERVER_URL` | URL GitLab |
| `CI_JOB_TOKEN` | Token automatico |

Non hai bisogno di passare `--repo` e `--pr` — vengono presi automaticamente dalla CI.

---

## Risultato della Review

### Note (commenti)

AI Review pubblica commenti sulla MR come note.

### Discussioni (inline)

Per commenti inline, hai bisogno di un token PAT completo (non `CI_JOB_TOKEN`).

I commenti inline appaiono direttamente accanto alle righe di codice nella vista diff.

### Summary

Alla fine della revisione, viene pubblicata una nota Summary con:

- Statistiche generali
- Metriche
- Good practice

---

## Troubleshooting

### La Review Non Pubblica Commenti

**Controlla:**

1. La variabile `AI_REVIEWER_GOOGLE_API_KEY` (o `GOOGLE_API_KEY`) e impostata
2. `AI_REVIEWER_GITLAB_TOKEN` (o `GITLAB_TOKEN`) ha permessi sufficienti (scope: `api`)
3. La pipeline e in esecuzione per una MR (non per un branch)

### "401 Unauthorized"

**Causa:** Token non valido.

**Soluzione:**

- Controlla che il token non sia scaduto
- Controlla lo scope (serve `api`)

### "403 Forbidden"

**Causa:** Permessi insufficienti.

**Soluzione:**

- Usa PAT invece di `CI_JOB_TOKEN`
- Controlla che il token abbia accesso al progetto

### "404 Not Found"

**Causa:** MR non trovata.

**Soluzione:**

- Controlla che la pipeline sia in esecuzione per una MR
- Controlla `CI_MERGE_REQUEST_IID`

### Rate Limit (429)

**Causa:** Limite API superato.

**Soluzione:**

- AI Code Reviewer riprova automaticamente con backoff esponenziale
- Se persiste — aspetta o aumenta i limiti

---

## Best Practice

### 1. Usa PAT per funzionalita completa

```yaml
variables:
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_TOKEN  # PAT, non CI_JOB_TOKEN
```

### 2. Aggiungi allow_failure

```yaml
allow_failure: true
```

La MR non verra bloccata se la revisione fallisce.

### 3. Imposta timeout

```yaml
timeout: 10m
```

### 4. Rendi il job interrompibile

```yaml
interruptible: true
```

La vecchia revisione verra cancellata con un nuovo commit.

### 5. Non aspettare altri stage

```yaml
needs: []
```

La revisione partira immediatamente, senza aspettare build/test.

---

## Prossimo Passo

- [Integrazione GitHub →](github.md)
- [Riferimento CLI →](api.md)
