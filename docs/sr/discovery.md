# Analiza projekta (Discovery)

AI ReviewBot uključuje automatski sistem **Project Discovery** koji analizira vaš repozitorijum prije svakog pregleda koda. Discovery uči vaš stack, CI pipeline i konvencije kako bi recenzent mogao dati pametnije i manje ometajuće povratne informacije.

---

## Kako funkcioniše

Discovery pokreće **4-slojni pipeline** na prvom PR/MR:

| Sloj | Izvor | Cijena |
|------|-------|--------|
| **Sloj 0** — Platform API | Jezici, stablo fajlova, tagovi sa GitHub/GitLab API | Besplatno (samo API) |
| **Sloj 1** — CI analiza | Parsiranje GitHub Actions / GitLab CI / Makefile | Besplatno (lokalno parsiranje) |
| **Sloj 2** — Config fajlovi | Čitanje `pyproject.toml`, `package.json`, linter konfiguracija | Besplatno (čitanje fajlova) |
| **Sloj 3** — LLM interpretacija | AI interpretira nejasne podatke (samo kada slojevi 0-2 nijesu dovoljni) | ~50-200 tokena |

Svaki sloj degradira elegantno — ako jedan zakaže, pipeline nastavlja sa onim što ima.

---

## Attention Zones

Discovery klasifikuje svaku oblast kvaliteta u jednu od tri **Attention Zones** na osnovu pokrivenosti vašeg CI/alatki:

| Zona | Emoji | Značenje | Ponašanje recenzenta |
|------|-------|----------|----------------------|
| **Well Covered** | ✅ | CI alati pokrivaju ovu oblast | Recenzent **preskače** |
| **Weakly Covered** | ⚠️ | Djelimična pokrivenost, prostor za poboljšanje | Recenzent **obraća pažnju** + predlaže poboljšanja |
| **Not Covered** | ❌ | Automatizacija nije detektovana | Recenzent **se fokusira** na ovu oblast |

### Primjeri zona

| Oblast | Status | Razlog |
|--------|--------|--------|
| Formatting | ✅ Well Covered | ruff format u CI |
| Type checking | ✅ Well Covered | mypy --strict u CI |
| Security scanning | ❌ Not Covered | Nema security skenera u CI |
| Test coverage | ⚠️ Weakly Covered | pytest se pokreće ali nema coverage praga |

---

## Šta se dešava automatski

1. **Discovery analizira** vaš repozitorijum (jezici, CI alati, config fajlovi).
2. **Attention Zones se izračunavaju** — svaka oblast kvaliteta se klasifikuje kao Well Covered, Weakly Covered ili Not Covered.
3. **Prompt za pregled se obogaćuje** instrukcijama zasnovanim na zonama (~200-400 tokena).
4. **Recenzent preskače** Well Covered oblasti i **fokusira se** na Not Covered oblasti.

### Discovery komentar

Ako Discovery pronađe **praznine** ili nepokrivene zone, objavljuje jednokratni sumarni komentar na PR/MR:

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

U **verbose režimu** (`discovery_verbose=true`), komentar takođe uključuje Well Covered zone:

> ### Well Covered (skipping in review)
> - ✅ **Formatting** — ruff format in CI
> - ✅ **Type checking** — mypy --strict in CI

---

## Watch-Files i keširanje (Caching)

Discovery koristi **watch-files** da izbjegne ponovno pokretanje LLM analize kada se konfiguracija projekta nije promijenila.

### Kako funkcioniše

1. **Prvo pokretanje:** Discovery izvršava puni pipeline, LLM vraća listu `watch_files` (npr. `pyproject.toml`, `.github/workflows/tests.yml`).
2. **Naredna pokretanja:** Discovery hešira svaki watch-file i poredi sa keširanim snimkom.
3. **Ako se ništa nije promijenilo:** koristi se keširani rezultat — **0 LLM tokena** potrošeno.
4. **Ako se promijenilo:** LLM ponovo analizira projekat.

To znači da ponovljeni PR-ovi na istoj grani koštaju **nula dodatnih tokena** za discovery, sve dok se nadgledani konfiguracioni fajlovi nijesu promijenili.

!!! tip "Ušteda tokena"
    Na tipičnom projektu, drugi i naredni PR-ovi troše 0 tokena za discovery. Samo promjene u CI konfiguraciji, `pyproject.toml`, `package.json` ili sličnim fajlovima pokreću novi LLM poziv.

---

## `discover` CLI komanda

Možete pokrenuti discovery samostalno (bez kreiranja pregleda) koristeći `discover` komandu:

```bash
ai-review discover owner/repo
```

### Opcije

| Opcija | Kratko | Opis | Podrazumijevano |
|--------|--------|------|-----------------|
| `--provider` | `-p` | Git provajder | `github` |
| `--json` | | Izlaz u JSON formatu | `false` |
| `--verbose` | `-v` | Prikaži sve detalje (konvencije, CI alati, watch-files) | `false` |

### Primjeri

```bash
# Osnovna analiza
ai-review discover owner/repo

# JSON izlaz za skriptovanje
ai-review discover owner/repo --json

# Verbose sa svim detaljima
ai-review discover owner/repo --verbose

# GitLab projekat
ai-review discover group/project -p gitlab
```

!!! info "Kompatibilnost unazad"
    `ai-review` (bez subkomande) i dalje pokreće pregled kao i ranije. `discover` subkomanda je nova.

---

## `.reviewbot.md`

Kreirajte `.reviewbot.md` fajl u korijenu repozitorijuma da biste pružili eksplicitan kontekst projekta. Kada ovaj fajl postoji, Discovery **preskače automatizovani pipeline** i koristi vašu konfiguraciju direktno.

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

### Sekcije

| Sekcija | Svrha |
|---------|-------|
| **Stack** | Primarni jezik, verzija, framework, paket menadžer, layout |
| **Automated Checks** | Alati koji već rade u CI (recenzent će preskočiti ove oblasti) |
| **Review Guidance → Skip** | Specifične oblasti koje recenzent ne treba komentarisati |
| **Review Guidance → Focus** | Oblasti kojima želite dodatnu pažnju |
| **Review Guidance → Conventions** | Pravila specifična za projekat koja recenzent treba primjenjivati |

!!! tip "Auto-generisanje"
    Možete pustiti Discovery da se pokrene jednom, zatim kopirati rezultate u `.reviewbot.md` i prilagoditi po potrebi. Bot uključuje link u podnožju koji predlaže ovaj tok rada.

---

## Konfiguracija

| Varijabla | Podrazumijevano | Opis |
|-----------|-----------------|------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | `true` | Aktivirati ili deaktivirati analizu projekta |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | `false` | Uvijek objaviti discovery komentar (podrazumijevano: samo pri prazninama/nepokrivenim zonama) |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | `30` | Timeout discovery pipeline-a u sekundama (1-300) |

Postavite `AI_REVIEWER_DISCOVERY_ENABLED` na `false` da potpuno preskočite discovery. Recenzent će i dalje raditi, ali bez konteksta projekta.

```yaml
# GitHub Actions — deaktivacija discovery-ja
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
    discovery_enabled: 'false'
```

---

## Tihi režim (Silent Mode)

Discovery komentar **se ne objavljuje** kada:

1. **`.reviewbot.md` postoji** u repozitorijumu — bot pretpostavlja da ste ga već konfigurisali.
2. **Nema praznina i nepokrivenih zona** — sve je Well Covered, nema pitanja za postaviti.
3. **Detekcija duplikata** — discovery komentar je već objavljen na ovom PR/MR.

U sva tri slučaja, discovery i dalje radi i obogaćuje prompt za pregled — samo ne objavljuje vidljivi komentar.

---

## FAQ

### Mogu li deaktivirati discovery?

Da. Postavite `AI_REVIEWER_DISCOVERY_ENABLED=false`. Recenzent će raditi bez konteksta projekta, isto kao prije dodavanja Discovery funkcionalnosti.

### Da li discovery košta dodatne LLM tokene?

Na **prvom pokretanju**: Slojevi 0-2 su besplatni (API pozivi i lokalno parsiranje). Sloj 3 (LLM interpretacija) se poziva samo kada prva tri sloja nijesu dovoljna — obično 50-200 tokena, što je zanemarljivo u poređenju sa samom revizijom (~1.500 tokena).

Na **narednim pokretanjima**: ako se vaši watch-files nijesu promijenili, discovery koristi **keširani rezultat** i košta **0 tokena**.

### Mogu li urediti automatski generisani `.reviewbot.md`?

Da, naravno. Fajl je dizajniran za ručno uređivanje. Mijenjajte šta god trebate — parser toleriše dodatni sadržaj i sekcije koje nedostaju.

### Da li se discovery pokreće na svakom PR?

Discovery obogaćuje prompt za pregled na svakom PR. **LLM poziv** je keširan putem watch-files (0 tokena kada se ništa nije promijenilo). **Discovery komentar** se objavljuje samo jednom (detekcija duplikata sprečava ponovljene objave).

### Kako da vidim sve zone uključujući Well Covered?

Postavite `AI_REVIEWER_DISCOVERY_VERBOSE=true`. Ovo primorava discovery komentar da se uvijek objavi i uključuje sve zone (Well Covered, Weakly Covered, Not Covered).

### Šta ako discovery traje predugo?

Postavite `AI_REVIEWER_DISCOVERY_TIMEOUT` na veću vrijednost (podrazumijevano: 30 sekundi, maksimalno: 300). Ako discovery prekorači timeout, pregled nastavlja bez discovery konteksta.

---

## Sljedeći korak

- [Konfiguracija →](configuration.md)
- [GitHub integracija →](github.md)
- [GitLab integracija →](gitlab.md)
