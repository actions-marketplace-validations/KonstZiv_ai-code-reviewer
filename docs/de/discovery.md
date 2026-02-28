# Projektanalyse (Discovery)

AI ReviewBot enthält ein automatisches **Project Discovery**-System, das Ihr Repository vor jedem Code-Review analysiert. Discovery erkennt Ihren Stack, Ihre CI-Pipeline und Konventionen, damit der Reviewer intelligenteres und weniger störendes Feedback geben kann.

---

## Wie es funktioniert

Discovery führt eine **4-Schichten-Pipeline** beim ersten PR/MR aus:

| Schicht | Quelle | Kosten |
|---------|--------|--------|
| **Schicht 0** — Platform API | Sprachen, Dateibaum, Topics von GitHub/GitLab API | Kostenlos (nur API) |
| **Schicht 1** — CI-Analyse | Parsing von GitHub Actions / GitLab CI / Makefile | Kostenlos (lokales Parsing) |
| **Schicht 2** — Config-Dateien | Lesen von `pyproject.toml`, `package.json`, Linter-Configs | Kostenlos (Datei-Reads) |
| **Schicht 3** — LLM-Interpretation | KI interpretiert mehrdeutige Daten (nur wenn Schichten 0-2 nicht ausreichen) | ~50-200 Tokens |

Jede Schicht degradiert sanft — wenn eine fehlschlägt, fährt die Pipeline mit dem fort, was sie hat.

---

## Attention Zones

Discovery klassifiziert jeden Qualitätsbereich in eine von drei **Attention Zones** basierend auf Ihrer CI-/Tooling-Abdeckung:

| Zone | Emoji | Bedeutung | Reviewer-Verhalten |
|------|-------|-----------|-------------------|
| **Well Covered** | :white_check_mark: | CI-Tools decken diesen Bereich ab | Reviewer **überspringt** ihn |
| **Weakly Covered** | :warning: | Teilweise Abdeckung, Verbesserungspotenzial | Reviewer **achtet darauf** + schlägt Verbesserungen vor |
| **Not Covered** | :x: | Keine Automatisierung erkannt | Reviewer **fokussiert** sich auf diesen Bereich |

### Beispiel-Zones

| Bereich | Status | Grund |
|---------|--------|-------|
| Formatting | :white_check_mark: Well Covered | ruff format in CI |
| Type checking | :white_check_mark: Well Covered | mypy --strict in CI |
| Security scanning | :x: Not Covered | No security scanner in CI |
| Test coverage | :warning: Weakly Covered | pytest runs but no coverage threshold |

---

## Was automatisch passiert

1. **Discovery analysiert** Ihr Repository (Sprachen, CI-Tools, Config-Dateien).
2. **Attention Zones werden berechnet** — jeder Qualitätsbereich wird als Well Covered, Weakly Covered oder Not Covered klassifiziert.
3. **Der Review-Prompt wird angereichert** mit zonengesteuerten Anweisungen (~200-400 Tokens).
4. **Der Reviewer überspringt** Well Covered Bereiche und **fokussiert** sich auf Not Covered Bereiche.

### Discovery-Kommentar

Wenn Discovery **Lücken** oder nicht abgedeckte Zones findet, postet es einen einmaligen Zusammenfassungskommentar im PR/MR:

> ## :mag: AI ReviewBot: Project Analysis
>
> **Stack:** Python (FastAPI) 3.13, uv
>
> **CI:** :white_check_mark: .github/workflows/tests.yml — ruff, mypy, pytest
>
> ### Not Covered (focusing in review)
> - :x: **Security scanning** — No security scanner detected in CI
>   :bulb: Consider adding bandit or safety to your pipeline
>
> ### Could Be Improved
> - :warning: **Test coverage** — pytest runs but no coverage threshold enforced
>   :bulb: Add `--cov-fail-under=80` to enforce minimum coverage
>
> **Questions / Gaps:**
> - No security scanner detected in CI
>   *Question:* Do you use any security scanning tools?
>   *Assumption:* Will check for common vulnerabilities manually
>
> ---
> :bulb: *Create `.reviewbot.md` in your repo root to customize.*

Im **Verbose-Modus** (`discovery_verbose=true`) enthält der Kommentar auch Well Covered Zones:

> ### Well Covered (skipping in review)
> - :white_check_mark: **Formatting** — ruff format in CI
> - :white_check_mark: **Type checking** — mypy --strict in CI

---

## Watch-Files & Caching

Discovery verwendet **watch-files**, um eine erneute LLM-Analyse zu vermeiden, wenn sich die Projektkonfiguration nicht geändert hat.

### Wie es funktioniert

1. **Erster Durchlauf:** Discovery führt die vollständige Pipeline aus, LLM liefert eine `watch_files`-Liste (z.B. `pyproject.toml`, `.github/workflows/tests.yml`).
2. **Nachfolgende Durchläufe:** Discovery hasht jede watch-file und vergleicht mit dem gecachten Snapshot.
3. **Wenn unverändert:** Das gecachte Ergebnis wird verwendet — **0 LLM-Tokens** verbraucht.
4. **Wenn geändert:** LLM analysiert das Projekt erneut.

Das bedeutet, wiederholte PRs auf demselben Branch kosten **keine zusätzlichen Tokens** für Discovery, solange sich die überwachten Konfigurationsdateien nicht geändert haben.

!!! tip "Token-Einsparungen"
    Bei einem typischen Projekt verwenden der zweite und alle weiteren PRs 0 Tokens für Discovery. Nur Änderungen an CI-Config, `pyproject.toml`, `package.json` oder ähnlichen Dateien lösen einen neuen LLM-Aufruf aus.

---

## `discover` CLI-Befehl

Sie können Discovery eigenständig ausführen (ohne ein Review zu erstellen) mit dem `discover`-Befehl:

```bash
ai-review discover owner/repo
```

### Optionen

| Option | Kurz | Beschreibung | Standard |
|--------|------|--------------|----------|
| `--provider` | `-p` | Git-Provider | `github` |
| `--json` | | Ausgabe als JSON | `false` |
| `--verbose` | `-v` | Alle Details anzeigen (Conventions, CI-Tools, watch-files) | `false` |

### Beispiele

```bash
# Einfache Discovery
ai-review discover owner/repo

# JSON-Ausgabe für Skripting
ai-review discover owner/repo --json

# Verbose mit allen Details
ai-review discover owner/repo --verbose

# GitLab-Projekt
ai-review discover group/project -p gitlab
```

!!! info "Abwärtskompatibilität"
    `ai-review` (ohne Subcommand) führt wie bisher ein Review durch. Der `discover`-Subcommand ist neu.

---

## `.reviewbot.md`

Erstellen Sie eine `.reviewbot.md`-Datei im Repository-Root, um expliziten Projektkontext bereitzustellen. Wenn diese Datei existiert, **überspringt Discovery die automatisierte Pipeline** und verwendet Ihre Konfiguration direkt.

### Format

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

### Abschnitte

| Abschnitt | Zweck |
|-----------|-------|
| **Stack** | Primärsprache, Version, Framework, Paketmanager, Layout |
| **Automated Checks** | Tools, die bereits in CI laufen (der Reviewer überspringt diese Bereiche) |
| **Review Guidance -> Skip** | Spezifische Bereiche, die der Reviewer nicht kommentieren soll |
| **Review Guidance -> Focus** | Bereiche, die besondere Aufmerksamkeit verdienen |
| **Review Guidance -> Conventions** | Projektspezifische Regeln, die der Reviewer einhalten soll |

!!! tip "Auto-Generierung"
    Sie können Discovery einmal laufen lassen, dann die Ergebnisse in `.reviewbot.md` kopieren und nach Bedarf anpassen. Der Bot enthält einen Footer-Link, der diesen Workflow vorschlägt.

---

## Konfiguration

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | `true` | Projektanalyse aktivieren oder deaktivieren |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | `false` | Discovery-Kommentar immer posten (Standard: nur bei Lücken/nicht abgedeckten Zones) |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | `30` | Discovery-Pipeline-Timeout in Sekunden (1-300) |

Setzen Sie `AI_REVIEWER_DISCOVERY_ENABLED` auf `false`, um Discovery komplett zu überspringen. Der Reviewer funktioniert weiterhin, aber ohne projektspezifischen Kontext.

```yaml
# GitHub Actions — Discovery deaktivieren
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
    discovery_enabled: 'false'
```

---

## Stiller Modus (Silent Mode)

Der Discovery-Kommentar wird **nicht gepostet** wenn:

1. **`.reviewbot.md` existiert** im Repository — der Bot nimmt an, dass Sie ihn bereits konfiguriert haben.
2. **Keine Lücken und keine nicht abgedeckten Zones** — alles ist Well Covered, keine Fragen zu stellen.
3. **Duplikaterkennung** — ein Discovery-Kommentar wurde bereits in diesem PR/MR gepostet.

In allen drei Fällen läuft Discovery trotzdem und reichert den Review-Prompt an — es wird nur kein sichtbarer Kommentar gepostet.

---

## FAQ

### Kann ich Discovery deaktivieren?

Ja. Setzen Sie `AI_REVIEWER_DISCOVERY_ENABLED=false`. Der Reviewer arbeitet dann ohne Projektkontext, genau wie vor der Einführung des Discovery-Features.

### Kostet Discovery zusätzliche LLM-Tokens?

Beim **ersten Durchlauf**: Schichten 0-2 sind kostenlos (API-Aufrufe und lokales Parsing). Schicht 3 (LLM-Interpretation) wird nur aufgerufen, wenn die ersten drei Schichten nicht ausreichen — typischerweise 50-200 Tokens, was im Vergleich zum Review selbst (~1.500 Tokens) vernachlässigbar ist.

Bei **nachfolgenden Durchläufen**: Wenn sich Ihre watch-files nicht geändert haben, verwendet Discovery das **gecachte Ergebnis** und kostet **0 Tokens**.

### Kann ich die auto-generierte `.reviewbot.md` bearbeiten?

Ja, absolut. Die Datei ist für manuelle Bearbeitung gedacht. Ändern Sie alles, was Sie brauchen — der Parser toleriert zusätzlichen Inhalt und fehlende Abschnitte.

### Läuft Discovery bei jedem PR?

Discovery reichert den Review-Prompt bei jedem PR an. Der **LLM-Aufruf** wird über watch-files gecacht (0 Tokens wenn unverändert). Der **Discovery-Kommentar** wird nur einmal gepostet (Duplikaterkennung verhindert wiederholte Posts).

### Wie kann ich alle Zones einschließlich Well Covered sehen?

Setzen Sie `AI_REVIEWER_DISCOVERY_VERBOSE=true`. Dies erzwingt, dass der Discovery-Kommentar immer gepostet wird und alle Zones enthält (Well Covered, Weakly Covered, Not Covered).

### Was tun, wenn Discovery zu lange dauert?

Setzen Sie `AI_REVIEWER_DISCOVERY_TIMEOUT` auf einen höheren Wert (Standard: 30 Sekunden, Maximum: 300). Wenn Discovery das Timeout überschreitet, fährt das Review ohne Discovery-Kontext fort.

---

## Nächster Schritt

- [Konfiguration →](configuration.md)
- [GitHub-Integration →](github.md)
- [GitLab-Integration →](gitlab.md)
