# Schnellstart

Starten Sie AI Code Reviewer in 5 Minuten auf GitHub oder GitLab.

---

## Schritt 1: API-Schlüssel erhalten

AI Reviewer benötigt einen Google Gemini API-Schlüssel.

1. Gehen Sie zu [Google AI Studio](https://aistudio.google.com/)
2. Melden Sie sich mit Ihrem Google-Konto an
3. Klicken Sie auf **"Get API key"** → **"Create API key"**
4. Kopieren Sie den Schlüssel (beginnt mit `AIza...`)

!!! warning "Schlüssel speichern"
    Der Schlüssel wird nur einmal angezeigt. Speichern Sie ihn an einem sicheren Ort.

!!! tip "Kostenlose Stufe"
    Gemini API hat eine kostenlose Stufe: 15 Anfragen pro Minute, ausreichend für die meisten Projekte.

---

## Schritt 2: Schlüssel zur Repository-Umgebung hinzufügen

Der Schlüssel muss als geheime Variable in Ihrem Repository hinzugefügt werden.

=== "GitHub"

    **Pfad:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    | Feld | Wert |
    |------|------|
    | **Name** | `GOOGLE_API_KEY` |
    | **Secret** | Ihr Schlüssel (`AIza...`) |

    Klicken Sie auf **"Add secret"**.

    ??? info "Detaillierte Anleitung mit Screenshots"
        1. Öffnen Sie Ihr Repository auf GitHub
        2. Klicken Sie auf **Settings** (Zahnrad im oberen Menü)
        3. Finden Sie im linken Menü **Secrets and variables** → **Actions**
        4. Klicken Sie auf die grüne Schaltfläche **New repository secret**
        5. Geben Sie im Feld **Name** ein: `GOOGLE_API_KEY`
        6. Fügen Sie im Feld **Secret** Ihren Schlüssel ein
        7. Klicken Sie auf **Add secret**

    :material-book-open-variant: [Offizielle GitHub-Dokumentation: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    Für GitLab müssen Sie einen **Project Access Token** erstellen und zwei Variablen hinzufügen.

    ### Schritt 2a: Project Access Token erstellen

    !!! note "Maintainer-Rechte erforderlich"
        Zum Erstellen eines Project Access Token benötigen Sie die Rolle **Maintainer** oder **Owner** im Projekt.

        :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

    **Pfad:** Project → `Settings` → `Access Tokens`

    | Feld | Wert |
    |------|------|
    | **Token name** | `ai-reviewer` |
    | **Expiration date** | Wählen Sie ein Datum (max. 1 Jahr) |
    | **Role** | `Developer` |
    | **Scopes** | :white_check_mark: `api` |

    Klicken Sie auf **"Create project access token"** → **Kopieren Sie den Token** (wird nur einmal angezeigt!)

    :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Schritt 2b: Variablen zu CI/CD hinzufügen

    **Pfad:** Project → `Settings` → `CI/CD` → `Variables`

    Fügen Sie **zwei** Variablen hinzu:

    | Key | Value | Flags |
    |-----|-------|-------|
    | `GOOGLE_API_KEY` | Ihr Gemini-Schlüssel (`AIza...`) | :white_check_mark: Mask variable |
    | `GITLAB_TOKEN` | Token aus Schritt 2a | :white_check_mark: Mask variable |

    ??? info "Detaillierte Anleitung"
        1. Öffnen Sie Ihr Projekt auf GitLab
        2. Gehen Sie zu **Settings** → **CI/CD**
        3. Erweitern Sie den Abschnitt **Variables**
        4. Klicken Sie auf **Add variable**
        5. Fügen Sie `GOOGLE_API_KEY` hinzu:
            - Key: `GOOGLE_API_KEY`
            - Value: Ihr Gemini API-Schlüssel
            - Flags: Mask variable ✓
        6. Klicken Sie auf **Add variable**
        7. Wiederholen Sie für `GITLAB_TOKEN`:
            - Key: `GITLAB_TOKEN`
            - Value: Token aus Schritt 2a
            - Flags: Mask variable ✓

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Schritt 3: AI Review zu CI hinzufügen {#ci-setup}

=== "GitHub"

    ### Variante A: Neue Workflow-Datei

    Wenn Sie GitHub Actions noch nicht verwenden oder eine separate Datei für AI Review möchten:

    1. Erstellen Sie den Ordner `.github/workflows/` im Stammverzeichnis des Repositorys (falls nicht vorhanden)
    2. Erstellen Sie die Datei `ai-review.yml` in diesem Ordner
    3. Kopieren Sie diesen Code:

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
        # Nicht für Fork-PRs ausführen (kein Zugriff auf Secrets)
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

    !!! info "Über `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` ist ein **automatischer Token**, den GitHub für jeden Workflow-Run erstellt. Sie müssen ihn **nicht** manuell zu den Secrets hinzufügen — er ist bereits verfügbar.

        Die Token-Berechtigungen werden durch den `permissions`-Abschnitt in der Workflow-Datei definiert.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

    4. Committen und pushen Sie die Datei

    ### Variante B: Zu bestehendem Workflow hinzufügen

    Wenn Sie bereits `.github/workflows/` mit anderen Jobs haben, fügen Sie diesen Job zu einer bestehenden Datei hinzu:

    ```yaml
    # Fügen Sie diesen Job zu Ihrer bestehenden Workflow-Datei hinzu
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

    !!! note "Trigger überprüfen"
        Stellen Sie sicher, dass Ihr Workflow `on: pull_request` unter den Triggern hat.

=== "GitLab"

    ### Variante A: Neue CI-Datei

    Wenn Sie noch keine `.gitlab-ci.yml` haben:

    1. Erstellen Sie die Datei `.gitlab-ci.yml` im Stammverzeichnis des Repositorys
    2. Kopieren Sie diesen Code:

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

    3. Committen und pushen Sie die Datei

    ### Variante B: Zu bestehendem CI hinzufügen

    Wenn Sie bereits eine `.gitlab-ci.yml` haben:

    1. Fügen Sie `review` zur Liste der `stages` hinzu (falls ein separater Stage benötigt wird)
    2. Fügen Sie diesen Job hinzu:

    ```yaml
    ai-review:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      stage: review  # oder test, oder ein anderer bestehender Stage
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

## Schritt 4: Ergebnis überprüfen

Jetzt wird AI Review automatisch ausgeführt bei:

| Plattform | Ereignis |
|-----------|----------|
| **GitHub** | PR erstellen, neue Commits im PR, PR wiedereröffnen |
| **GitLab** | MR erstellen, neue Commits im MR |

### Was Sie sehen werden

Nach Abschluss des CI-Jobs erscheinen im PR/MR:

- **Inline-Kommentare** — an bestimmte Codezeilen gebunden
- **"Apply suggestion"-Button** — zum schnellen Anwenden von Korrekturen (GitHub)
- **Summary-Kommentar** — allgemeine Übersicht mit Metriken

Jeder Kommentar enthält:

- :red_circle: / :yellow_circle: / :blue_circle: Schweregrad-Badge
- Problembeschreibung
- Korrekturvorschlag
- Aufklappbaren Abschnitt "Warum ist das wichtig?"

---

## Fehlerbehebung

### Review erscheint nicht?

Checkliste überprüfen:

- [ ] `GOOGLE_API_KEY` als Secret hinzugefügt?
- [ ] `github_token` explizit übergeben? (für GitHub)
- [ ] CI-Job erfolgreich abgeschlossen? (Logs überprüfen)
- [ ] Für GitHub: hat `permissions: pull-requests: write`?
- [ ] Für Fork-PRs: Secrets sind nicht verfügbar — das ist erwartetes Verhalten

### In den Logs wird `--help` angezeigt?

Das bedeutet, dass die CLI die erforderlichen Parameter nicht erhalten hat. Überprüfen Sie:

- Wurde `github_token` / `GITLAB_TOKEN` explizit übergeben
- Ist das YAML-Format korrekt (Einrückung!)

### Rate Limit?

Gemini Free Tier: 15 Anfragen pro Minute. Warten Sie eine Minute und versuchen Sie es erneut.

:point_right: [Alle Probleme und Lösungen →](troubleshooting.md)

---

## Was kommt als Nächstes?

| Aufgabe | Dokument |
|---------|----------|
| Antwortsprache konfigurieren | [Konfiguration](configuration.md) |
| Erweiterte GitHub-Einstellungen | [GitHub-Leitfaden](github.md) |
| Erweiterte GitLab-Einstellungen | [GitLab-Leitfaden](gitlab.md) |
| Workflow-Beispiele | [Beispiele](examples/index.md) |
