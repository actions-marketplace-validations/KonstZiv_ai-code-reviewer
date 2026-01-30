# GitLab

Guida dettagliata per l'integrazione con GitLab CI.

---

## Token di Accesso {#tokens}

### Project Access Token {#get-token}

Per funzionare, AI Reviewer necessita di un **Project Access Token** con permessi per creare commenti.

!!! note "Ruolo Maintainer richiesto"
    Per creare un Project Access Token, e necessario il ruolo **Maintainer** o **Owner** nel progetto.

    :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

**Creazione del token:**

1. Apri il progetto → `Settings` → `Access Tokens`
2. Clicca **Add new token**
3. Compila il form:

| Campo | Valore |
|-------|--------|
| **Token name** | `ai-reviewer` |
| **Expiration date** | Scegli una data (max 1 anno) |
| **Role** | `Developer` |
| **Scopes** | :white_check_mark: `api` |

4. Clicca **Create project access token**
5. **Copia il token** — viene mostrato una sola volta!

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # Da CI/CD Variables
```

!!! warning "Salva il token"
    GitLab mostra il token **una sola volta**. Salvalo immediatamente.

:material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

---

## Variabili CI/CD

### Aggiungere Variabili

`Settings → CI/CD → Variables → Add variable`

| Variabile | Valore | Opzioni |
|-----------|--------|---------|
| `GOOGLE_API_KEY` | Chiave API Gemini | Masked |
| `GITLAB_TOKEN` | Project Access Token | Masked |

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
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
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
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
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
  GITLAB_URL: https://gitlab.mycompany.com
  GOOGLE_API_KEY: $GOOGLE_API_KEY
  GITLAB_TOKEN: $GITLAB_TOKEN
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

Non hai bisogno di passare `--project` e `--mr-iid` — vengono presi automaticamente dalla CI.

---

## Risultato della Review

### Note (commenti)

AI Review pubblica commenti sulla MR come note.

### Discussioni (inline)

Per commenti inline serve un Project Access Token con scope `api`.

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

1. La variabile `GOOGLE_API_KEY` e impostata
2. `GITLAB_TOKEN` ha permessi sufficienti (scope: `api`)
3. La pipeline e in esecuzione per una MR (non per un branch)

### "401 Unauthorized"

**Causa:** Token non valido.

**Soluzione:**

- Controlla che il token non sia scaduto
- Controlla lo scope (serve `api`)

### "403 Forbidden"

**Causa:** Permessi insufficienti.

**Soluzione:**

- Usa un Project Access Token con scope `api`
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
  GITLAB_TOKEN: $GITLAB_TOKEN  # Project Access Token
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
