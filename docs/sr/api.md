# CLI referenca

Referenca komandi AI Code Reviewer-a.

---

## Glavna komanda

```bash
ai-review [OPTIONS]
```

**Ponašanje:**

- U CI (GitHub Actions / GitLab CI) — automatski prepoznaje kontekst
- Ručno — potrebno je navesti `--provider`, `--repo`, `--pr`

---

## Opcije

| Opcija | Kratko | Opis | Podrazumijevano |
|--------|-------|-------------|---------|
| `--provider` | `-p` | CI provajder | Auto-detekcija |
| `--repo` | `-r` | Repozitorijum (owner/repo) | Auto-detekcija |
| `--pr` | | PR/MR broj | Auto-detekcija |
| `--help` | | Prikaži pomoć | |
| `--version` | | Prikaži verziju | |

---

## Provajderi

| Vrijednost | Opis |
|-------|-------------|
| `github` | GitHub (GitHub Actions) |
| `gitlab` | GitLab (GitLab CI) |

---

## Primjeri upotrebe

### U CI (automatski)

```bash
# GitHub Actions — sve automatski
ai-review

# GitLab CI — sve automatski
ai-review
```

### Ručno za GitHub

```bash
export GOOGLE_API_KEY=your_key
export GITHUB_TOKEN=your_token

ai-review --provider github --repo owner/repo --pr 123
```

<small>
**Odakle uzeti vrijednosti:**

- `--repo` — iz URL-a repozitorijuma: `github.com/owner/repo` → `owner/repo`
- `--pr` — broj iz URL-a: `github.com/owner/repo/pull/123` → `123`
</small>

### Ručno za GitLab

```bash
export GOOGLE_API_KEY=your_key
export GITLAB_TOKEN=your_token

ai-review --provider gitlab --repo owner/repo --pr 456
```

<small>
**Odakle uzeti vrijednosti:**

- `--repo` — putanja projekta iz URL-a: `gitlab.com/group/project` → `group/project`
- `--pr` — MR broj iz URL-a: `gitlab.com/group/project/-/merge_requests/456` → `456`
</small>

### Kratka sintaksa

```bash
ai-review -p github -r owner/repo --pr 123
```

---

## Varijable okruženja

CLI čita konfiguraciju iz varijabli okruženja:

### Obavezne

| Varijabla | Opis |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API ključ |
| `GITHUB_TOKEN` | GitHub token (za GitHub) |
| `GITLAB_TOKEN` | GitLab token (za GitLab) |

### Opcione

| Varijabla | Opis | Podrazumijevano |
|----------|-------------|---------|
| `LANGUAGE` | Jezik odgovora | `en` |
| `LANGUAGE_MODE` | Jezički režim | `adaptive` |
| `GEMINI_MODEL` | Gemini model | `gemini-2.5-flash` |
| `LOG_LEVEL` | Nivo logova | `INFO` |
| `GITLAB_URL` | GitLab URL | `https://gitlab.com` |

:point_right: [Puna lista →](configuration.md)

---

## Auto-detekcija

### GitHub Actions

CLI automatski koristi:

| Varijabla | Opis |
|----------|-------------|
| `GITHUB_ACTIONS` | Detekcija okruženja |
| `GITHUB_REPOSITORY` | owner/repo |
| `GITHUB_EVENT_PATH` | JSON sa detaljima PR-a |
| `GITHUB_REF` | Fallback za PR broj |

### GitLab CI

CLI automatski koristi:

| Varijabla | Opis |
|----------|-------------|
| `GITLAB_CI` | Detekcija okruženja |
| `CI_PROJECT_PATH` | owner/repo |
| `CI_MERGE_REQUEST_IID` | MR broj |
| `CI_SERVER_URL` | GitLab URL |

---

## Izlazni kodovi

| Kod | Opis |
|------|-------------|
| `0` | Uspjeh |
| `1` | Greška (konfiguracija, API, itd.) |

---

## Logovanje

### Nivoi

| Nivo | Opis |
|-------|-------------|
| `DEBUG` | Detaljne informacije za debagovanje |
| `INFO` | Opšte informacije (podrazumijevano) |
| `WARNING` | Upozorenja |
| `ERROR` | Greške |
| `CRITICAL` | Kritične greške |

### Konfiguracija

```bash
export LOG_LEVEL=DEBUG
ai-review
```

### Izlaz

CLI koristi [Rich](https://rich.readthedocs.io/) za formatirani izlaz:

```
[12:34:56] INFO     Detected CI Provider: github
[12:34:56] INFO     Context extracted: owner/repo PR #123
[12:34:57] INFO     Fetching PR diff...
[12:34:58] INFO     Analyzing code with Gemini...
[12:35:02] INFO     Review completed successfully
```

---

## Greške

### Greška konfiguracije

```
Configuration Error: GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Uzrok:** Nevažeća konfiguracija.

**Rješenje:** Provjerite varijable okruženja.

### Greška konteksta

```
Context Error: Could not determine PR number from GitHub Actions context.
```

**Uzrok:** Workflow se ne pokreće za PR.

**Rješenje:** Provjerite da workflow ima `on: pull_request`.

### Provajder nije prepoznat

```
Error: Could not detect CI environment.
Please specify --provider, --repo, and --pr manually.
```

**Uzrok:** Pokretanje izvan CI-ja.

**Rješenje:** Navedite sve parametre ručno.

---

## Docker

Pokretanje putem Docker-a:

```bash
docker run --rm \
  -e GOOGLE_API_KEY=your_key \
  -e GITHUB_TOKEN=your_token \
  ghcr.io/konstziv/ai-code-reviewer:1 \
  --provider github \
  --repo owner/repo \
  --pr 123
```

---

## Verzija

```bash
ai-review --version
```

```
AI Code Reviewer 0.1.0
```

---

## Pomoć

```bash
ai-review --help
```

```
Usage: ai-review [OPTIONS]

  Run AI Code Reviewer.

  Automatically detects CI environment and reviews the current Pull Request.
  Can also be run manually by providing arguments.

Options:
  -p, --provider [github|gitlab]  CI provider (auto-detected if not provided)
  -r, --repo TEXT                 Repository name (e.g. owner/repo). Auto-detected in CI.
  --pr INTEGER                    Pull Request number. Auto-detected in CI.
  --help                          Show this message and exit.
```

---

## Sljedeći korak

- [Rješavanje problema →](troubleshooting.md)
- [Primjeri →](examples/index.md)
