# Brzi početak

Pokrenite AI Code Reviewer za 5 minuta na GitHub-u ili GitLab-u.

---

## Korak 1: Preuzmite API ključ

Za rad AI Reviewer-a potreban je Google Gemini API ključ.

1. Idite na [Google AI Studio](https://aistudio.google.com/)
2. Prijavite se sa Google nalogom
3. Kliknite **"Get API key"** → **"Create API key"**
4. Kopirajte ključ (počinje sa `AIza...`)

!!! warning "Sačuvajte ključ"
    Ključ se prikazuje samo jednom. Sačuvajte ga na bezbjednom mjestu.

!!! tip "Besplatni nivo"
    Gemini API ima besplatni nivo: 15 zahtjeva po minuti, dovoljno za većinu projekata.

---

## Korak 2: Dodajte ključ u okruženje repozitorijuma

Ključ treba dodati kao tajnu varijablu u vašem repozitorijumu.

=== "GitHub"

    **Putanja:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    | Polje | Vrijednost |
    |------|----------|
    | **Name** | `GOOGLE_API_KEY` |
    | **Secret** | Vaš ključ (`AIza...`) |

    Kliknite **"Add secret"**.

    ??? info "Detaljna uputstva sa snimcima ekrana"
        1. Otvorite vaš repozitorijum na GitHub-u
        2. Kliknite **Settings** (zupčanik u gornjem meniju)
        3. U lijevom meniju pronađite **Secrets and variables** → **Actions**
        4. Kliknite zeleno dugme **New repository secret**
        5. U polje **Name** unesite: `GOOGLE_API_KEY`
        6. U polje **Secret** zalijepite vaš ključ
        7. Kliknite **Add secret**

    :material-book-open-variant: [Zvanična dokumentacija GitHub: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    Za GitLab trebate kreirati **Project Access Token** i dodati dvije varijable.

    ### Korak 2a: Kreirajte Project Access Token

    !!! note "Potrebna Maintainer prava"
        Za kreiranje Project Access Token-a potrebna je uloga **Maintainer** ili **Owner** u projektu.

        :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

    **Putanja:** Project → `Settings` → `Access Tokens`

    | Polje | Vrijednost |
    |------|----------|
    | **Token name** | `ai-reviewer` |
    | **Expiration date** | Izaberite datum (maks. 1 godina) |
    | **Role** | `Developer` |
    | **Scopes** | :white_check_mark: `api` |

    Kliknite **"Create project access token"** → **Kopirajte token** (prikazuje se samo jednom!)

    :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Korak 2b: Dodajte varijable u CI/CD

    **Putanja:** Project → `Settings` → `CI/CD` → `Variables`

    Dodajte **dvije** varijable:

    | Key | Value | Flags |
    |-----|-------|-------|
    | `GOOGLE_API_KEY` | Vaš Gemini ključ (`AIza...`) | :white_check_mark: Mask variable |
    | `GITLAB_TOKEN` | Token iz koraka 2a | :white_check_mark: Mask variable |

    ??? info "Detaljna uputstva"
        1. Otvorite vaš projekat na GitLab-u
        2. Idite na **Settings** → **CI/CD**
        3. Proširite sekciju **Variables**
        4. Kliknite **Add variable**
        5. Dodajte `GOOGLE_API_KEY`:
            - Key: `GOOGLE_API_KEY`
            - Value: vaš Gemini API ključ
            - Flags: Mask variable ✓
        6. Kliknite **Add variable**
        7. Ponovite za `GITLAB_TOKEN`:
            - Key: `GITLAB_TOKEN`
            - Value: token iz koraka 2a
            - Flags: Mask variable ✓

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Korak 3: Dodajte AI Review u CI {#ci-setup}

=== "GitHub"

    ### Opcija A: Novi workflow fajl

    Ako još ne koristite GitHub Actions, ili želite poseban fajl za AI Review:

    1. Kreirajte folder `.github/workflows/` u korijenu repozitorijuma (ako ne postoji)
    2. Kreirajte fajl `ai-review.yml` u tom folderu
    3. Kopirajte ovaj kod:

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
        # Ne pokreći za fork PR-ove (nema pristupa tajnama)
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

    !!! info "O `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` — ovo je **automatski token** koji GitHub kreira za svako pokretanje workflow-a. **Ne treba** ga dodavati u tajne ručno — već je dostupan.

        Prava tokena definisana su sekcijom `permissions` u workflow fajlu.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

    4. Komitujte i pušujte fajl

    ### Opcija B: Dodajte u postojeći workflow

    Ako već imate `.github/workflows/` sa drugim job-ovima, dodajte ovaj job u postojeći fajl:

    ```yaml
    # Dodajte ovaj job u vaš postojeći workflow fajl
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

    !!! note "Provjerite triggere"
        Uvjerite se da vaš workflow ima `on: pull_request` među trigerima.

=== "GitLab"

    ### Opcija A: Novi CI fajl

    Ako nemate `.gitlab-ci.yml`:

    1. Kreirajte fajl `.gitlab-ci.yml` u korijenu repozitorijuma
    2. Kopirajte ovaj kod:

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

    3. Komitujte i pušujte fajl

    ### Opcija B: Dodajte u postojeći CI

    Ako već imate `.gitlab-ci.yml`:

    1. Dodajte `review` na listu `stages` (ako je potreban poseban stage)
    2. Dodajte ovaj job:

    ```yaml
    ai-review:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      stage: review  # ili test, ili drugi postojeći stage
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

## Korak 4: Provjerite rezultat

Sada će se AI Review pokretati automatski pri:

| Platforma | Događaj |
|-----------|-------|
| **GitHub** | Kreiranje PR-a, novi komiti u PR-u, ponovno otvaranje PR-a |
| **GitLab** | Kreiranje MR-a, novi komiti u MR-u |

### Šta ćete vidjeti

Nakon završetka CI job-a, u PR/MR će se pojaviti:

- **Inline komentari** — povezani sa specifičnim linijama koda
- **Dugme "Apply suggestion"** — za brzu primjenu ispravki (GitHub)
- **Summary komentar** — opšti pregled sa metrikama

Svaki komentar sadrži:

- :red_circle: / :yellow_circle: / :blue_circle: Oznaku ozbiljnosti
- Opis problema
- Prijedlog ispravke
- Sklopivi odjeljak "Zašto je ovo važno?"

---

## Rješavanje problema

### Revizija se ne pojavljuje?

Provjerite listu:

- [ ] `GOOGLE_API_KEY` dodan kao tajna?
- [ ] `github_token` eksplicitno proslijeđen? (za GitHub)
- [ ] CI job završen uspješno? (provjerite logove)
- [ ] Za GitHub: ima li `permissions: pull-requests: write`?
- [ ] Za fork PR-ove: tajne nijesu dostupne — ovo je očekivano ponašanje

### U logovima se prikazuje `--help`?

Ovo znači da CLI nije dobio potrebne parametre. Provjerite:

- Da li je proslijeđen `github_token` / `GITLAB_TOKEN` eksplicitno
- Da li je YAML format ispravan (uvlačenja!)

### Rate limit?

Gemini free tier: 15 zahtjeva po minuti. Sačekajte minut i pokušajte ponovo.

:point_right: [Svi problemi i rješenja →](troubleshooting.md)

---

## Šta dalje?

| Zadatak | Dokument |
|--------|----------|
| Konfiguriši jezik odgovora | [Konfiguracija](configuration.md) |
| Napredna podešavanja GitHub | [GitHub vodič](github.md) |
| Napredna podešavanja GitLab | [GitLab vodič](gitlab.md) |
| Primjeri workflow-a | [Primjeri](examples/index.md) |
