# GitLab

Detaillierter Leitfaden für die Integration mit GitLab CI.

---

## Zugriffstoken {#tokens}

### Project Access Token {#get-token}

AI Reviewer benötigt einen **Project Access Token** mit Berechtigungen zum Erstellen von Kommentaren.

!!! note "Maintainer-Rolle erforderlich"
    Um einen Project Access Token zu erstellen, benötigen Sie die Rolle **Maintainer** oder **Owner** im Projekt.

    :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

**Token erstellen:**

1. Öffnen Sie Projekt → `Settings` → `Access Tokens`
2. Klicken Sie auf **Add new token**
3. Füllen Sie das Formular aus:

| Feld | Wert |
|------|------|
| **Token name** | `ai-reviewer` |
| **Expiration date** | Wählen Sie ein Datum (max. 1 Jahr) |
| **Role** | `Developer` |
| **Scopes** | :white_check_mark: `api` |

4. Klicken Sie auf **Create project access token**
5. **Kopieren Sie den Token** — er wird nur einmal angezeigt!

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # Aus CI/CD Variables
```

!!! warning "Token speichern"
    GitLab zeigt den Token **nur einmal** an. Speichern Sie ihn sofort.

:material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

---

## CI/CD-Variablen

### Variablen hinzufügen

`Settings → CI/CD → Variables → Add variable`

| Variable | Wert | Optionen |
|----------|------|----------|
| `GOOGLE_API_KEY` | Gemini API-Schlüssel | Masked |
| `GITLAB_TOKEN` | Project Access Token | Masked |

!!! tip "Masked"
    Aktivieren Sie immer **Masked** für Secrets — sie werden nicht in Logs angezeigt.

---

## Trigger

### Empfohlener Trigger

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Dies führt den Job nur für Merge-Request-Pipelines aus.

### Alternativer Trigger (only/except)

```yaml
only:
  - merge_requests
```

!!! note "rules vs only"
    `rules` — neuere Syntax, von GitLab empfohlen.

---

## Job-Beispiele

### Minimal

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

### Vollständig (empfohlen)

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

**Was es bewirkt:**

- `allow_failure: true` — MR wird nicht blockiert, wenn Review fehlschlägt
- `timeout: 10m` — maximal 10 Minuten
- `interruptible: true` — kann bei neuem Commit abgebrochen werden

### Mit benutzerdefinierter Stage

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
  needs: []  # Nicht auf vorherige Stages warten
```

---

## Self-hosted GitLab

### Konfiguration

```yaml
variables:
  GITLAB_URL: https://gitlab.mycompany.com
  GOOGLE_API_KEY: $GOOGLE_API_KEY
  GITLAB_TOKEN: $GITLAB_TOKEN
```

### Docker Registry

Wenn Ihr GitLab keinen Zugriff auf `ghcr.io` hat, erstellen Sie einen Mirror:

```bash
# Auf einer Maschine mit Zugriff
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

## GitLab CI-Variablen

AI Code Reviewer verwendet automatisch:

| Variable | Beschreibung |
|----------|--------------|
| `CI_PROJECT_PATH` | `owner/repo` |
| `CI_MERGE_REQUEST_IID` | MR-Nummer |
| `CI_SERVER_URL` | GitLab-URL |

Sie müssen `--project` und `--mr-iid` nicht übergeben — sie werden automatisch aus CI übernommen.

---

## Review-Ergebnis

### Notes (Kommentare)

AI Review postet Kommentare zum MR als Notes.

### Discussions (Inline)

Für Inline-Kommentare benötigen Sie einen Project Access Token mit Scope `api`.

Inline-Kommentare erscheinen direkt neben Code-Zeilen in der Diff-Ansicht.

### Zusammenfassung

Am Ende des Reviews wird eine Zusammenfassungs-Note gepostet mit:

- Gesamtstatistik
- Metriken
- Gute Praktiken

---

## Fehlerbehebung

### Review postet keine Kommentare

**Überprüfen:**

1. `GOOGLE_API_KEY`-Variable ist gesetzt
2. `GITLAB_TOKEN` hat ausreichende Berechtigungen (Scope: `api`)
3. Pipeline läuft für MR (nicht für einen Branch)

### "401 Unauthorized"

**Ursache:** Ungültiger Token.

**Lösung:**

- Überprüfen Sie, ob der Token nicht abgelaufen ist
- Überprüfen Sie den Scope (benötigt `api`)

### "403 Forbidden"

**Ursache:** Unzureichende Berechtigungen.

**Lösung:**

- Verwenden Sie Project Access Token mit Scope `api`
- Überprüfen Sie, ob der Token Zugriff auf das Projekt hat

### "404 Not Found"

**Ursache:** MR nicht gefunden.

**Lösung:**

- Überprüfen Sie, ob die Pipeline für MR läuft
- Überprüfen Sie `CI_MERGE_REQUEST_IID`

### Rate Limit (429)

**Ursache:** API-Limit überschritten.

**Lösung:**

- AI Code Reviewer wiederholt automatisch mit Backoff
- Bei anhaltendem Problem — warten oder Limits erhöhen

---

## Best Practices

### 1. PAT für volle Funktionalität verwenden

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # Project Access Token
```

### 2. allow_failure hinzufügen

```yaml
allow_failure: true
```

MR wird nicht blockiert, wenn Review fehlschlägt.

### 3. Timeout setzen

```yaml
timeout: 10m
```

### 4. Job unterbrechbar machen

```yaml
interruptible: true
```

Altes Review wird bei neuem Commit abgebrochen.

### 5. Nicht auf andere Stages warten

```yaml
needs: []
```

Review startet sofort, ohne auf Build/Test zu warten.

---

## Nächster Schritt

- [GitHub-Integration →](github.md)
- [CLI-Referenz →](api.md)
