# Quick Start

Configura AI Code Reviewer in 5 minuti su GitHub o GitLab.

---

## Passo 1: Ottieni la Chiave API

Per funzionare, AI Reviewer necessita di una chiave API Google Gemini.

1. Vai su [Google AI Studio](https://aistudio.google.com/)
2. Accedi con il tuo account Google
3. Clicca **"Get API key"** → **"Create API key"**
4. Copia la chiave (inizia con `AIza...`)

!!! warning "Salva la chiave"
    La chiave viene mostrata una sola volta. Salvala in un posto sicuro.

!!! tip "Tier gratuito"
    L'API Gemini ha un tier gratuito: 15 richieste al minuto, sufficiente per la maggior parte dei progetti.

---

## Passo 2: Aggiungi la Chiave nell'Ambiente del Repository

La chiave deve essere aggiunta come variabile segreta nel tuo repository.

=== "GitHub"

    **Percorso:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    | Campo | Valore |
    |-------|--------|
    | **Name** | `GOOGLE_API_KEY` |
    | **Secret** | La tua chiave (`AIza...`) |

    Clicca **"Add secret"**.

    ??? info "Istruzioni dettagliate con screenshot"
        1. Apri il tuo repository su GitHub
        2. Clicca **Settings** (ingranaggio nel menu superiore)
        3. Nel menu a sinistra trova **Secrets and variables** → **Actions**
        4. Clicca il pulsante verde **New repository secret**
        5. Nel campo **Name** inserisci: `GOOGLE_API_KEY`
        6. Nel campo **Secret** incolla la tua chiave
        7. Clicca **Add secret**

    :material-book-open-variant: [Documentazione ufficiale GitHub: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    Per GitLab devi creare un **Project Access Token** e aggiungere due variabili.

    ### Passo 2a: Crea un Project Access Token

    !!! note "Servono i permessi Maintainer"
        Per creare un Project Access Token serve il ruolo **Maintainer** o **Owner** nel progetto.

        :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

    **Percorso:** Project → `Settings` → `Access Tokens`

    | Campo | Valore |
    |-------|--------|
    | **Token name** | `ai-reviewer` |
    | **Expiration date** | Scegli una data (max 1 anno) |
    | **Role** | `Developer` |
    | **Scopes** | :white_check_mark: `api` |

    Clicca **"Create project access token"** → **Copia il token** (viene mostrato una sola volta!)

    :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Passo 2b: Aggiungi le Variabili in CI/CD

    **Percorso:** Project → `Settings` → `CI/CD` → `Variables`

    Aggiungi **due** variabili:

    | Key | Value | Flags |
    |-----|-------|-------|
    | `GOOGLE_API_KEY` | La tua chiave Gemini (`AIza...`) | :white_check_mark: Mask variable |
    | `GITLAB_TOKEN` | Token dal passo 2a | :white_check_mark: Mask variable |

    ??? info "Istruzioni dettagliate"
        1. Apri il tuo progetto su GitLab
        2. Vai su **Settings** → **CI/CD**
        3. Espandi la sezione **Variables**
        4. Clicca **Add variable**
        5. Aggiungi `GOOGLE_API_KEY`:
            - Key: `GOOGLE_API_KEY`
            - Value: la tua chiave API Gemini
            - Flags: Mask variable ✓
        6. Clicca **Add variable**
        7. Ripeti per `GITLAB_TOKEN`:
            - Key: `GITLAB_TOKEN`
            - Value: token dal passo 2a
            - Flags: Mask variable ✓

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Passo 3: Aggiungi AI Review nel CI {#ci-setup}

=== "GitHub"

    ### Opzione A: Nuovo file workflow

    Se non usi ancora GitHub Actions, o vuoi un file separato per AI Review:

    1. Crea la cartella `.github/workflows/` nella root del repository (se non esiste)
    2. Crea il file `ai-review.yml` in questa cartella
    3. Copia questo codice:

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
        # Non eseguire per PR da fork (nessun accesso ai secret)
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

    !!! info "Info su `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` e un **token automatico** che GitHub crea per ogni workflow run. **Non serve** aggiungerlo manualmente ai secret — e gia disponibile.

        I permessi del token sono definiti dalla sezione `permissions` nel file workflow.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

    4. Committa e pusha il file

    ### Opzione B: Aggiungi a un workflow esistente

    Se hai gia `.github/workflows/` con altri job, aggiungi questo job al file esistente:

    ```yaml
    # Aggiungi questo job al tuo file workflow esistente
    ai-review:
      runs-on: ubuntu-latest
      if: github.event_name == 'pull_request' && github.event.pull_request.head.repo.full_name == github.repository
      permissions:
        contents: read
        pull-requests: write
      steps:
        - uses: KonstZiv/ai-code-reviewer@v1
          with:
            github_token: ${{ secrets.GITHUB_TOKEN }}
            google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    ```

    !!! note "Controlla i trigger"
        Assicurati che il tuo workflow abbia `on: pull_request` tra i trigger.

=== "GitLab"

    ### Opzione A: Nuovo file CI

    Se non hai ancora `.gitlab-ci.yml`:

    1. Crea il file `.gitlab-ci.yml` nella root del repository
    2. Copia questo codice:

    ```yaml
    stages:
      - review

    ai-review:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      stage: review
      script:
        - ai-review
      rules:
        - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      allow_failure: true
      variables:
        GITLAB_TOKEN: $GITLAB_TOKEN
        GOOGLE_API_KEY: $GOOGLE_API_KEY
    ```

    3. Committa e pusha il file

    ### Opzione B: Aggiungi a CI esistente

    Se hai gia `.gitlab-ci.yml`:

    1. Aggiungi `review` alla lista `stages` (se serve uno stage separato)
    2. Aggiungi questo job:

    ```yaml
    ai-review:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      stage: review  # o test, o un altro stage esistente
      script:
        - ai-review
      rules:
        - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      allow_failure: true
      variables:
        GITLAB_TOKEN: $GITLAB_TOKEN
        GOOGLE_API_KEY: $GOOGLE_API_KEY
    ```

---

## Passo 4: Verifica il Risultato

Ora AI Review partira automaticamente quando:

| Piattaforma | Evento |
|-------------|--------|
| **GitHub** | Creazione PR, nuovi commit in PR, riapertura PR |
| **GitLab** | Creazione MR, nuovi commit in MR |

### Cosa Vedrai

Dopo il completamento del job CI, appariranno nel PR/MR:

- **Commenti inline** — collegati a righe specifiche di codice
- **Pulsante "Apply suggestion"** — per applicare rapidamente le correzioni (GitHub)
- **Commento summary** — panoramica generale con metriche

Ogni commento contiene:

- :red_circle: / :yellow_circle: / :blue_circle: Badge di gravita
- Descrizione del problema
- Suggerimento di correzione
- Sezione espandibile "Perche e importante?"

---

## Troubleshooting

### La revisione non appare?

Controlla questa checklist:

- [ ] `GOOGLE_API_KEY` aggiunto come secret?
- [ ] `github_token` passato esplicitamente? (per GitHub)
- [ ] Il job CI e terminato con successo? (controlla i log)
- [ ] Per GitHub: hai `permissions: pull-requests: write`?
- [ ] Per PR da fork: i secret non sono disponibili — comportamento previsto

### Nei log appare `--help`?

Significa che la CLI non ha ricevuto i parametri necessari. Controlla:

- Se `github_token` / `GITLAB_TOKEN` e passato esplicitamente
- Se il formato YAML e corretto (indentazione!)

### Rate limit?

Gemini free tier: 15 richieste al minuto. Aspetta un minuto e riprova.

:point_right: [Tutti i problemi e soluzioni →](troubleshooting.md)

---

## Cosa Fare Dopo?

| Compito | Documento |
|---------|-----------|
| Configurare la lingua delle risposte | [Configurazione](configuration.md) |
| Impostazioni avanzate GitHub | [Guida GitHub](github.md) |
| Impostazioni avanzate GitLab | [Guida GitLab](gitlab.md) |
| Esempi di workflow | [Esempi](examples/index.md) |
