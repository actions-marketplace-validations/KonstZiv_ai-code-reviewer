# GitLab

Detailed guide for integration with GitLab CI.

---

## Access Token {#tokens}

### Project Access Token {#get-token}

AI Reviewer needs a **Project Access Token** with permissions to create comments.

!!! note "Maintainer role required"
    To create a Project Access Token, you need the **Maintainer** or **Owner** role in the project.

    :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

**Creating the token:**

1. Open the project → `Settings` → `Access Tokens`
2. Click **Add new token**
3. Fill in the form:

| Field | Value |
|-------|-------|
| **Token name** | `ai-reviewer` |
| **Expiration date** | Choose a date (max 1 year) |
| **Role** | `Developer` |
| **Scopes** | :white_check_mark: `api` |

4. Click **Create project access token**
5. **Copy the token** — it's shown only once!

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # From CI/CD Variables
```

!!! warning "Save the token"
    GitLab shows the token **only once**. Save it immediately.

:material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

---

## CI/CD Variables

### Adding Variables

`Settings → CI/CD → Variables → Add variable`

| Variable | Value | Options |
|----------|-------|---------|
| `GOOGLE_API_KEY` | Gemini API key | Masked |
| `GITLAB_TOKEN` | Project Access Token | Masked |

!!! tip "Masked"
    Always enable **Masked** for secrets — they won't be shown in logs.

---

## Triggers

### Recommended Trigger

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

This runs the job only for Merge Request pipelines.

### Alternative Trigger (only/except)

```yaml
only:
  - merge_requests
```

!!! note "rules vs only"
    `rules` — newer syntax, recommended by GitLab.

---

## Job Examples

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

### Full (recommended)

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

**What it does:**

- `allow_failure: true` — MR is not blocked if review fails
- `timeout: 10m` — maximum 10 minutes
- `interruptible: true` — can be cancelled on new commit

### With Custom Stage

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
  needs: []  # Don't wait for previous stages
```

---

## Self-hosted GitLab

### Configuration

```yaml
variables:
  GITLAB_URL: https://gitlab.mycompany.com
  GOOGLE_API_KEY: $GOOGLE_API_KEY
  GITLAB_TOKEN: $GITLAB_TOKEN
```

### Docker Registry

If your GitLab doesn't have access to `ghcr.io`, create a mirror:

```bash
# On a machine with access
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

## GitLab CI Variables

AI Code Reviewer automatically uses:

| Variable | Description |
|----------|-------------|
| `CI_PROJECT_PATH` | `owner/repo` |
| `CI_MERGE_REQUEST_IID` | MR number |
| `CI_SERVER_URL` | GitLab URL |

You don't need to pass `--project` and `--mr-iid` — they're taken from CI automatically.

---

## Review Result

### Notes (comments)

AI Review posts comments to MR as notes.

### Discussions (inline)

For inline comments you need a Project Access Token with scope `api`.

Inline comments appear directly next to code lines in the diff view.

### Summary

At the end of the review, a Summary note is posted with:

- Overall statistics
- Metrics
- Good practices

---

## Troubleshooting

### Review Not Posting Comments

**Check:**

1. `GOOGLE_API_KEY` variable is set
2. `GITLAB_TOKEN` has sufficient permissions (scope: `api`)
3. Pipeline is running for MR (not for a branch)

### "401 Unauthorized"

**Cause:** Invalid token.

**Solution:**

- Check that the token is not expired
- Check scope (need `api`)

### "403 Forbidden"

**Cause:** Insufficient permissions.

**Solution:**

- Use Project Access Token with scope `api`
- Check that the token has access to the project

### "404 Not Found"

**Cause:** MR not found.

**Solution:**

- Check that the pipeline is running for MR
- Check `CI_MERGE_REQUEST_IID`

### Rate Limit (429)

**Cause:** API limit exceeded.

**Solution:**

- AI Code Reviewer automatically retries with backoff
- If persistent — wait or increase limits

---

## Best Practices

### 1. Use PAT for full functionality

```yaml
variables:
  GITLAB_TOKEN: $GITLAB_TOKEN  # Project Access Token
```

### 2. Add allow_failure

```yaml
allow_failure: true
```

MR won't be blocked if review fails.

### 3. Set timeout

```yaml
timeout: 10m
```

### 4. Make job interruptible

```yaml
interruptible: true
```

Old review will be cancelled on new commit.

### 5. Don't wait for other stages

```yaml
needs: []
```

Review will start immediately, without waiting for build/test.

---

## Next Step

- [GitHub integration →](github.md)
- [CLI Reference →](api.md)
