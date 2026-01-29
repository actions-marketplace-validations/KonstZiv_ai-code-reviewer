# AI ReviewBot

**Assistente basato su AI per la revisione automatica del codice nella tua pipeline CI/CD.**

---

## Cos'e?

AI Code Reviewer e uno strumento che analizza automaticamente le tue Pull Request (GitHub) e Merge Request (GitLab), trova problemi e suggerisce correzioni con un pulsante **"Apply Suggestion"**.
In sostanza, ottieni il punto di vista imparziale di uno sviluppatore senior sul tuo codice insieme a suggerimenti per migliorarlo.

E possibile l'integrazione con un'ampia gamma di provider LLM esistenti (di default **Google Gemini**, modello **gemini-2.5-flash** — al momento dell'attuale release, i limiti di utilizzo del tier gratuito per richieste al minuto e al giorno sono sufficienti per un flusso di lavoro normale di un team di 4-8 sviluppatori a tempo pieno).


---

## Cosa ottieni?


- :white_check_mark: **Commenti sul Codice** — valutazione generale del codice e raccomandazioni
- :white_check_mark: **Allineamento al Task** — allineamento del PR/MR con il contesto del task
- :white_check_mark: **Commenti Inline** — commenti direttamente sulle righe di codice
- :white_check_mark: **Apply Suggestion** — pulsante one-click per applicare le correzioni
- :white_check_mark: **Spiegazioni di Mentoring** — perche e importante + link alle risorse
- :white_check_mark: **Adattivita Linguistica** — rileva la lingua dal contesto PR/MR
- :white_check_mark: **Metriche** — tempo di esecuzione, token
- :white_check_mark: **Resilienza** — logica di retry per errori 429/5xx

---

## Quick Start

Importante: per seguire i prossimi passi avrai bisogno della tua chiave API Google personale. Puoi ottenerla gratuitamente su [Google AI Studio](https://aistudio.google.com/api-keys) o [Google Cloud Console](https://console.cloud.google.com/).

*AI Code Reviewer puo essere configurato per usare diversi provider LLM e modelli, sia gratuiti che a pagamento. I seguenti esempi usano il modello* **gemini-2.5-flash**. *Altre sezioni della documentazione spiegano come collegare altri provider e usare altri modelli. Siamo interessati alla tua opinione sulle differenze tra i vari modelli — ci piacerebbe leggere la tua esperienza nei commenti.*


### GitHub


Nel tuo repository, crea:
- in `Settings` → `Secrets and variables [Security]` → `Actions` → premi `New repository secret`:
    - crea un secret chiamato `GOOGLE_API_KEY` con la tua chiave API Google come valore.
- nella root del repository del tuo progetto:
    - crea il file `.github/workflows/ai-review.yml` con il seguente contenuto:

```yaml
# .github/workflows/ai-review.yml
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

### GitLab

Nel tuo repository, crea:
- in `Settings` → `CI/CD` → `Variables` → `CI/CD Variables` → premi `Add variable`:
    - `Type`: Variable (default)
    - `Visibility`: Masked (cosi non viene mostrato nei log)
    - `Key`: GOOGLE_API_KEY
    - `Value`: la tua chiave API Google
- nella root del repository del tuo progetto:
    - crea il file `.gitlab-ci.yml` con il seguente contenuto:

```yaml
# .gitlab-ci.yml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

:point_right: [Scopri di piu →](quick-start.md)


Crea un nuovo PR/MR — ottieni una revisione.

**La qualita della revisione dipende direttamente dalla comprensione delle tue intenzioni da parte di AI Code Reviewer** (proprio come con un revisore umano reale). Pertanto, e una buona idea accompagnare il processo di sviluppo con la documentazione:
- crea un issue che descrive il problema e i risultati desiderati
- crea un branch collegato/PR/MR collegato nell'issue, descrivendo il problema in modo piu dettagliato, l'approccio alla soluzione, i vincoli, i risultati desiderati, i casi limite — tutto cio che aggiunge comprensione del contesto, strumenti, risultati
- se lavori in team — comunica negli issue, commenta i PR/MR — tutto questo aggiunge contesto e migliora la qualita della revisione

---

## Piattaforme Supportate

| Piattaforma | Stato | Integrazione |
|-------------|-------|--------------|
| **GitHub** | :white_check_mark: | GitHub Actions / GitHub Action |
| **GitLab** | :white_check_mark: | GitLab CI / Immagine Docker |
| **Self-hosted** | :white_check_mark: | Docker / PyPI |

---

## Come funziona?

```mermaid
graph TD
    A[PR/MR creato] --> B[CI esegue AI Review]
    B --> C[Ottieni diff + contesto]
    C --> D[Analizza con Gemini]
    D --> E[Pubblica Commenti Inline]
    E --> F[Pulsante Apply Suggestion]
```

**Passo dopo passo:**

1. Crei un PR/MR
2. La pipeline CI esegue AI Code Reviewer
3. Lo strumento recupera diff, descrizione PR, task collegato
4. Gemini analizza il codice e genera raccomandazioni
5. I risultati vengono pubblicati come commenti inline con pulsante "Apply"

---

## Esempio di Revisione

!!! danger "🔴 CRITICO: Secret Hardcoded"
    **File:** `config.py:15`

    Chiave API hardcoded trovata nel codice.

    ```suggestion
    API_KEY = os.getenv("API_KEY")
    ```

    ??? info "Perche e importante?"
        I secret nel codice finiscono nella cronologia git e possono essere rubati.
        Usa variabili d'ambiente o secret manager.

        :link: [OWASP: Hardcoded Credentials](https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password)

---

## Categorie di Problemi

| Categoria | Descrizione |
|-----------|-------------|
| :lock: **Sicurezza** | Vulnerabilita, secret hardcoded |
| :memo: **Qualita del Codice** | Leggibilita, naming, DRY |
| :building_construction: **Architettura** | SOLID, design pattern |
| :zap: **Performance** | N+1, algoritmi inefficienti |
| :test_tube: **Testing** | Copertura, casi limite |

---

## Installazione

=== "Docker (consigliato)"

    ```bash
    docker pull ghcr.io/konstziv/ai-code-reviewer:1
    ```

=== "PyPI"

    ```bash
    pip install ai-reviewbot
    ```

=== "Sorgente"

    ```bash
    git clone https://github.com/KonstZiv/ai-code-reviewer.git
    cd ai-code-reviewer
    uv sync
    ```

:point_right: [Scopri di piu →](installation.md)

---

## Configurazione

Configurazione minima — solo la chiave API:

```bash
export GOOGLE_API_KEY=your_api_key
```

Opzioni aggiuntive:

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `LANGUAGE` | Lingua delle risposte (ISO 639) | `en` |
| `LANGUAGE_MODE` | `adaptive` / `fixed` | `adaptive` |
| `GEMINI_MODEL` | Modello Gemini | `gemini-2.0-flash` |
| `LOG_LEVEL` | Livello di logging | `INFO` |

:point_right: [Tutte le opzioni →](configuration.md)

---

## Documentazione

<div class="grid cards" markdown>

-   :rocket: **[Quick Start](quick-start.md)**

    Istruzioni copia-incolla per GitHub e GitLab

-   :gear: **[Configurazione](configuration.md)**

    Tutte le variabili d'ambiente e opzioni

-   :octicons-mark-github-16: **[GitHub](github.md)**

    Permessi, secret, suggerimenti workflow

-   :simple-gitlab: **[GitLab](gitlab.md)**

    Job token, trigger MR, self-hosted

-   :material-console: **[Riferimento CLI](api.md)**

    Comandi e parametri

-   :material-lifebuoy: **[Troubleshooting](troubleshooting.md)**

    FAQ e risoluzione problemi

</div>

---

## Costi

AI Code Reviewer usa **Google Gemini 2.5 Flash** — in modalita Free Tier. I limiti (alla data di release) sono 500 RPD. Questo e sufficiente per servire PR/MR per un team di 4-8 sviluppatori a tempo pieno, incluse sia revisioni che commenti significativi (senza flood e off-topic).
Se usi il tier a pagamento (Pay-as-you-go), il costo di una revisione tipica e conversazioni illimitate:

| Metrica | Costo |
|---------|-------|
| Token in input | $0.30 / 1M |
| Token in output | $2.5 / 1M |
| **Revisione tipica** | **~$0.003 - $0.01** |

:bulb: ~1000 revisioni = ~$3 ... ~$10

---

## Licenza

Apache 2.0 — libero di usare, modificare e distribuire.

---

## Supporto

- :bug: [GitHub Issues](https://github.com/KonstZiv/ai-code-reviewer/issues) — bug e suggerimenti
- :speech_balloon: [GitHub Discussions](https://github.com/KonstZiv/ai-code-reviewer/discussions) — domande e discussioni

---

**Pronto a migliorare le tue code review?** :point_right: [Inizia →](quick-start.md)
