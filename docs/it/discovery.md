# Analisi del progetto (Discovery)

AI ReviewBot include un sistema automatico di **Project Discovery** che analizza il tuo repository prima di ogni revisione del codice. Discovery impara il tuo stack, la pipeline CI e le convenzioni in modo che il revisore possa fornire feedback più intelligente e meno rumoroso.

---

## Come funziona

Discovery esegue una **pipeline a 4 livelli** al primo PR/MR:

| Livello | Fonte | Costo |
|---------|-------|-------|
| **Livello 0** — Platform API | Linguaggi, albero file, topic da GitHub/GitLab API | Gratuito (solo API) |
| **Livello 1** — Analisi CI | Parsing di GitHub Actions / GitLab CI / Makefile | Gratuito (parsing locale) |
| **Livello 2** — File di config | Lettura di `pyproject.toml`, `package.json`, config dei linter | Gratuito (lettura file) |
| **Livello 3** — Interpretazione LLM | L'IA interpreta dati ambigui (solo quando i livelli 0-2 sono insufficienti) | ~50-200 token |

Ogni livello degrada gradualmente — se uno fallisce, la pipeline continua con ciò che ha.

---

## Attention Zones

Discovery classifica ogni area di qualità in una delle tre **Attention Zones** in base alla copertura CI/tooling:

| Zona | Emoji | Significato | Comportamento revisore |
|------|-------|-------------|------------------------|
| **Well Covered** | ✅ | Gli strumenti CI gestiscono quest'area | Il revisore la **salta** |
| **Weakly Covered** | ⚠️ | Copertura parziale, margini di miglioramento | Il revisore **presta attenzione** + suggerisce miglioramenti |
| **Not Covered** | ❌ | Nessuna automazione rilevata | Il revisore **si concentra** su quest'area |

### Esempio di zone

| Area | Stato | Motivo |
|------|-------|--------|
| Formatting | ✅ Well Covered | ruff format in CI |
| Type checking | ✅ Well Covered | mypy --strict in CI |
| Security scanning | ❌ Not Covered | Nessuno scanner di sicurezza in CI |
| Test coverage | ⚠️ Weakly Covered | pytest eseguito ma nessuna soglia di copertura |

---

## Cosa succede automaticamente

1. **Discovery analizza** il tuo repository (linguaggi, strumenti CI, file di config).
2. **Le Attention Zones vengono calcolate** — ogni area di qualità viene classificata come Well Covered, Weakly Covered o Not Covered.
3. **Il prompt di revisione viene arricchito** con istruzioni basate sulle zone (~200-400 token).
4. **Il revisore salta** le aree Well Covered e **si concentra** su quelle Not Covered.

### Commento Discovery

Se Discovery trova **lacune** o zone non coperte, pubblica un commento riassuntivo una tantum nel PR/MR:

> ## 🔍 AI ReviewBot: Project Analysis
>
> **Stack:** Python (FastAPI) 3.13, uv
>
> **CI:** ✅ .github/workflows/tests.yml — ruff, mypy, pytest
>
> ### Not Covered (focusing in review)
> - ❌ **Security scanning** — No security scanner detected in CI
>   💡 Consider adding bandit or safety to your pipeline
>
> ### Could Be Improved
> - ⚠️ **Test coverage** — pytest runs but no coverage threshold enforced
>   💡 Add `--cov-fail-under=80` to enforce minimum coverage
>
> **Questions / Gaps:**
> - No security scanner detected in CI
>   *Question:* Do you use any security scanning tools?
>   *Assumption:* Will check for common vulnerabilities manually
>
> ---
> 💡 *Create `.reviewbot.md` in your repo root to customize.*

In **verbose mode** (`discovery_verbose=true`), il commento include anche le zone Well Covered:

> ### Well Covered (skipping in review)
> - ✅ **Formatting** — ruff format in CI
> - ✅ **Type checking** — mypy --strict in CI

---

## Watch-Files & Caching

Discovery usa i **watch-files** per evitare di rieseguire l'analisi LLM quando la configurazione del progetto non è cambiata.

### Come funziona

1. **Prima esecuzione:** Discovery esegue la pipeline completa, LLM restituisce una lista `watch_files` (es., `pyproject.toml`, `.github/workflows/tests.yml`).
2. **Esecuzioni successive:** Discovery calcola l'hash di ogni watch-file e lo confronta con lo snapshot in cache.
3. **Se invariato:** viene usato il risultato in cache — **0 token LLM** consumati.
4. **Se modificato:** LLM riesegue l'analisi del progetto.

Ciò significa che PR ripetuti sullo stesso branch costano **zero token aggiuntivi** per il discovery, purché i file di configurazione monitorati non siano cambiati.

!!! tip "Risparmio token"
    In un progetto tipico, il secondo PR e i successivi usano 0 token per il discovery. Solo modifiche alla configurazione CI, `pyproject.toml`, `package.json` o file simili attivano una nuova chiamata LLM.

---

## Comando `discover` (CLI)

Puoi eseguire il discovery standalone (senza creare una review) usando il comando `discover`:

```bash
ai-review discover owner/repo
```

### Opzioni

| Opzione | Abbreviazione | Descrizione | Default |
|---------|---------------|-------------|---------|
| `--provider` | `-p` | Provider Git | `github` |
| `--json` | | Output in formato JSON | `false` |
| `--verbose` | `-v` | Mostra tutti i dettagli (convenzioni, strumenti CI, watch-files) | `false` |

### Esempi

```bash
# Discovery di base
ai-review discover owner/repo

# Output JSON per scripting
ai-review discover owner/repo --json

# Verbose con tutti i dettagli
ai-review discover owner/repo --verbose

# Progetto GitLab
ai-review discover group/project -p gitlab
```

!!! info "Retrocompatibilità"
    `ai-review` (senza subcommand) esegue comunque una review come prima. Il subcommand `discover` è nuovo.

---

## `.reviewbot.md`

Crea un file `.reviewbot.md` nella root del repository per fornire un contesto esplicito del progetto. Quando questo file esiste, Discovery **salta la pipeline automatizzata** e usa la tua configurazione direttamente.

### Formato

```markdown
<!-- Auto-generated by AI ReviewBot. Feel free to edit. -->
# .reviewbot.md

## Stack
- **Language:** Python 3.13
- **Framework:** FastAPI
- **Package manager:** uv
- **Layout:** src

## Automated Checks
- **Linting:** ruff
- **Formatting:** ruff
- **Type checking:** mypy
- **Testing:** pytest
- **Security:** bandit
- **CI:** github_actions

## Review Guidance

### Skip (CI handles these)
- Import ordering (ruff handles isort rules)
- Code formatting and style (ruff format in CI)
- Type annotation completeness (mypy --strict in CI)

### Focus
- SQL injection and other OWASP Top 10 vulnerabilities
- API backward compatibility
- Business logic correctness

### Conventions
- All endpoints must return Pydantic response models
- Use dependency injection for database sessions
```

### Sezioni

| Sezione | Scopo |
|---------|-------|
| **Stack** | Linguaggio principale, versione, framework, gestore pacchetti, layout |
| **Automated Checks** | Strumenti già in esecuzione nella CI (il revisore salterà queste aree) |
| **Review Guidance → Skip** | Aree specifiche su cui il revisore non deve commentare |
| **Review Guidance → Focus** | Aree che vuoi ricevano attenzione extra |
| **Review Guidance → Conventions** | Regole specifiche del progetto che il revisore deve applicare |

!!! tip "Auto-generazione"
    Puoi lasciare che Discovery si esegua una volta, poi copiare i risultati in `.reviewbot.md` e adattare secondo necessità. Il bot include un link nel footer che suggerisce questo workflow.

---

## Configurazione

| Variabile | Predefinito | Descrizione |
|-----------|-------------|-------------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | `true` | Attivare o disattivare l'analisi del progetto |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | `false` | Pubblica sempre il commento discovery (default: solo in caso di lacune/zone non coperte) |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | `30` | Timeout della pipeline discovery in secondi (1-300) |

Imposta `AI_REVIEWER_DISCOVERY_ENABLED` a `false` per saltare completamente il discovery. Il revisore funzionerà comunque, ma senza contesto del progetto.

```yaml
# GitHub Actions — disabilitare il discovery
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
    discovery_enabled: 'false'
```

---

## Modalità silenziosa (Silent Mode)

Il commento discovery **non viene pubblicato** quando:

1. **`.reviewbot.md` esiste** nel repository — il bot presume che l'hai già configurato.
2. **Nessuna lacuna e nessuna zona non coperta** — tutto è Well Covered, nessuna domanda da fare.
3. **Rilevamento duplicati** — un commento discovery è già stato pubblicato in questo PR/MR.

In tutti e tre i casi, il discovery continua a funzionare e arricchisce il prompt di revisione — semplicemente non pubblica un commento visibile.

---

## FAQ

### Posso disattivare il discovery?

Sì. Imposta `AI_REVIEWER_DISCOVERY_ENABLED=false`. Il revisore funzionerà senza contesto del progetto, come prima dell'introduzione della funzionalità Discovery.

### Il discovery costa token LLM aggiuntivi?

Alla **prima esecuzione**: i livelli 0-2 sono gratuiti (chiamate API e parsing locale). Il livello 3 (interpretazione LLM) viene invocato solo quando i primi tre livelli non forniscono dati sufficienti — tipicamente 50-200 token, trascurabili rispetto alla review stessa (~1.500 token).

Alle **esecuzioni successive**: se i tuoi watch-files non sono cambiati, il discovery usa il **risultato in cache** e costa **0 token**.

### Posso modificare il `.reviewbot.md` auto-generato?

Sì, assolutamente. Il file è progettato per la modifica manuale. Cambia tutto ciò che serve — il parser tollera contenuto aggiuntivo e sezioni mancanti.

### Il discovery viene eseguito ad ogni PR?

Il discovery arricchisce il prompt di revisione ad ogni PR. La **chiamata LLM** è memorizzata in cache tramite watch-files (0 token quando invariato). Il **commento discovery** viene pubblicato solo una volta (il rilevamento duplicati previene pubblicazioni ripetute).

### Come vedo tutte le zone, comprese quelle Well Covered?

Imposta `AI_REVIEWER_DISCOVERY_VERBOSE=true`. Questo forza la pubblicazione del commento discovery e include tutte le zone (Well Covered, Weakly Covered, Not Covered).

### Cosa succede se il discovery impiega troppo tempo?

Imposta `AI_REVIEWER_DISCOVERY_TIMEOUT` a un valore più alto (default: 30 secondi, massimo: 300). Se il discovery supera il timeout, la review procede senza contesto del discovery.

---

## Prossimo passo

- [Configurazione →](configuration.md)
- [Integrazione GitHub →](github.md)
- [Integrazione GitLab →](gitlab.md)
