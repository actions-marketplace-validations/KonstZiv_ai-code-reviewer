# GitLab

Detailed guide for integration with GitLab CI.

---

## Tokens {#tokens}

### CI_JOB_TOKEN (automatic)

In GitLab CI, `CI_JOB_TOKEN` is automatically available:

```yaml
variables:
  AI_REVIEWER_GITLAB_TOKEN: $CI_JOB_TOKEN
```

**`CI_JOB_TOKEN` limitations:**

| Feature | Status |
|---------|--------|
| Read MR | :white_check_mark: |
| Read diff | :white_check_mark: |
| Post notes | :white_check_mark: |
| Create discussions | :x: |

!!! warning "Limited permissions"
    `CI_JOB_TOKEN` cannot create inline discussions.

    For full functionality, use a Personal Access Token.

### Personal Access Token (PAT) {#get-token}

For **all GitLab plans** (including Free). Recommended for local runs or full CI functionality.

**How to create:**

1. Go to **User Settings → Access Tokens → Add new token**
    - URL: `https://gitlab.com/-/user_settings/personal_access_tokens`
2. Fill in the fields:
    - **Token name:** `ai-code-reviewer`
    - **Expiration date:** set as needed (e.g., 1 year)
    - **Scopes:** check **`api`**
3. Click **Create personal access token**
4. **Copy the token immediately** — GitLab shows it only once!

**How to use in CI:**

1. Go to **Settings → CI/CD → Variables → Add variable**
2. Add variable:
    - **Key:** `AI_REVIEWER_GITLAB_TOKEN` (or `GITLAB_TOKEN`)
    - **Value:** paste your token
    - **Flags:** check **Masked** and **Protected**
3. Use in `.gitlab-ci.yml`:

```yaml
variables:
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_TOKEN  # Personal Access Token from CI/CD Variables
```

!!! warning "Save the token"
    GitLab shows the token **only once**. Save it in a secure location immediately.

### Project Access Token (:material-crown: Premium/Ultimate) {#project-token}

Available only on **GitLab Premium** and **Ultimate** plans. A good choice if you prefer a project-scoped token instead of a personal one.

**Advantages over PAT:**

- Scoped to a single project (no access to other projects)
- Can be revoked by project maintainers (no dependency on a specific user)
- Better for teams — not tied to a personal account

**How to create:**

1. Go to **Project → Settings → Access Tokens**
    - URL: `https://gitlab.com/<owner>/<repo>/-/settings/access_tokens`
2. Fill in the fields:
    - **Token name:** `ai-code-reviewer`
    - **Role:** `Developer` (minimum required)
    - **Scopes:** check **`api`**
3. Click **Create project access token**
4. **Copy the token immediately**

**How to use in CI:**

Same as PAT — add as `AI_REVIEWER_GITLAB_TOKEN` in CI/CD Variables:

```yaml
variables:
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_PROJECT_TOKEN  # Project Access Token from CI/CD Variables
```

!!! info "Which token to choose?"
    | | CI_JOB_TOKEN | Personal Access Token | Project Access Token |
    |---|---|---|---|
    | **Plan** | All | All (including Free) | Premium/Ultimate only |
    | **Setup** | Automatic | Manual | Manual |
    | **Scope** | Current job only | All user's projects | Single project |
    | **Inline comments** | :x: | :white_check_mark: | :white_check_mark: |
    | **Best for** | Quick start | Free plan + full features | Teams on Premium/Ultimate |

---

## CI/CD Variables

### Adding Variables

`Settings → CI/CD → Variables → Add variable`

| Variable | Value | Options |
|----------|-------|---------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Gemini API key | Masked |
| `AI_REVIEWER_GITLAB_TOKEN` | PAT (if needed) | Masked |

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
    AI_REVIEWER_GOOGLE_API_KEY: $GOOGLE_API_KEY
    AI_REVIEWER_GITLAB_TOKEN: $CI_JOB_TOKEN  # Automatic, no setup needed
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
    AI_REVIEWER_GOOGLE_API_KEY: $GOOGLE_API_KEY
    # Use CI_JOB_TOKEN (automatic) or a Personal Access Token for full permissions:
    AI_REVIEWER_GITLAB_TOKEN: $CI_JOB_TOKEN    # or: $GITLAB_PAT (see "Get Token" above)
    AI_REVIEWER_LANGUAGE: uk
    AI_REVIEWER_LANGUAGE_MODE: adaptive
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
  AI_REVIEWER_GITLAB_URL: https://gitlab.mycompany.com
  AI_REVIEWER_GOOGLE_API_KEY: $GOOGLE_API_KEY
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_TOKEN
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
| `CI_JOB_TOKEN` | Automatic token |

You don't need to pass `--repo` and `--pr` — they're taken from CI automatically.

---

## Review Result

### Notes (comments)

AI Review posts comments to MR as notes.

### Discussions (inline)

For inline comments, you need a full PAT token (not `CI_JOB_TOKEN`).

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

1. `AI_REVIEWER_GOOGLE_API_KEY` (or `GOOGLE_API_KEY`) variable is set
2. `AI_REVIEWER_GITLAB_TOKEN` (or `GITLAB_TOKEN`) has sufficient permissions (scope: `api`)
3. Pipeline is running for MR (not for a branch)

### "401 Unauthorized"

**Cause:** Invalid token.

**Solution:**

- Check that the token is not expired
- Check scope (need `api`)

### "403 Forbidden"

**Cause:** Insufficient permissions.

**Solution:**

- Use PAT instead of `CI_JOB_TOKEN`
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
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_TOKEN  # PAT, not CI_JOB_TOKEN
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
