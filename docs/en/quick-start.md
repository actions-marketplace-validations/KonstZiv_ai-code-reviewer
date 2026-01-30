# Quick Start

Get AI Code Reviewer running in 5 minutes on GitHub or GitLab.

---

## Step 1: Get an API Key

AI Reviewer needs a Google Gemini API key to work.

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **"Get API key"** → **"Create API key"**
4. Copy the key (it starts with `AIza...`)

!!! warning "Save the key"
    The key is shown only once. Save it in a secure place.

!!! tip "Free tier"
    Gemini API has a free tier: 15 requests per minute, sufficient for most projects.

---

## Step 2: Add the Key to Your Repository Environment

The key needs to be added as a secret variable in your repository.

=== "GitHub"

    **Path:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    | Field | Value |
    |-------|-------|
    | **Name** | `GOOGLE_API_KEY` |
    | **Secret** | Your key (`AIza...`) |

    Click **"Add secret"**.

    ??? info "Detailed instructions with screenshots"
        1. Open your repository on GitHub
        2. Click **Settings** (gear icon in the top menu)
        3. In the left menu find **Secrets and variables** → **Actions**
        4. Click the green **New repository secret** button
        5. In the **Name** field enter: `GOOGLE_API_KEY`
        6. In the **Secret** field paste your key
        7. Click **Add secret**

    :material-book-open-variant: [Official GitHub documentation: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    For GitLab you need to create a **Project Access Token** and add two variables.

    ### Step 2a: Create a Project Access Token

    !!! note "Maintainer rights required"
        To create a Project Access Token you need the **Maintainer** or **Owner** role in the project.

        :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

    **Path:** Project → `Settings` → `Access Tokens`

    | Field | Value |
    |-------|-------|
    | **Token name** | `ai-reviewer` |
    | **Expiration date** | Choose a date (max 1 year) |
    | **Role** | `Developer` |
    | **Scopes** | :white_check_mark: `api` |

    Click **"Create project access token"** → **Copy the token** (shown only once!)

    :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Step 2b: Add Variables to CI/CD

    **Path:** Project → `Settings` → `CI/CD` → `Variables`

    Add **two** variables:

    | Key | Value | Flags |
    |-----|-------|-------|
    | `GOOGLE_API_KEY` | Your Gemini key (`AIza...`) | :white_check_mark: Mask variable |
    | `GITLAB_TOKEN` | Token from step 2a | :white_check_mark: Mask variable |

    ??? info "Detailed instructions"
        1. Open your project on GitLab
        2. Go to **Settings** → **CI/CD**
        3. Expand the **Variables** section
        4. Click **Add variable**
        5. Add `GOOGLE_API_KEY`:
            - Key: `GOOGLE_API_KEY`
            - Value: your Gemini API key
            - Flags: Mask variable ✓
        6. Click **Add variable**
        7. Repeat for `GITLAB_TOKEN`:
            - Key: `GITLAB_TOKEN`
            - Value: token from step 2a
            - Flags: Mask variable ✓

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Step 3: Add AI Review to CI {#ci-setup}

=== "GitHub"

    ### Option A: New workflow file

    If you're not using GitHub Actions yet, or want a separate file for AI Review:

    1. Create folder `.github/workflows/` in the repository root (if it doesn't exist)
    2. Create file `ai-review.yml` in that folder
    3. Copy this code:

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
        # Don't run for fork PRs (no access to secrets)
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

    !!! info "About `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` is an **automatic token** that GitHub creates for each workflow run. You **don't need** to add it to secrets manually — it's already available.

        Token permissions are defined by the `permissions` section in the workflow file.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

    4. Commit and push the file

    ### Option B: Add to existing workflow

    If you already have `.github/workflows/` with other jobs, add this job to your existing file:

    ```yaml
    # Add this job to your existing workflow file
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

    !!! note "Check triggers"
        Make sure your workflow has `on: pull_request` among the triggers.

=== "GitLab"

    ### Option A: New CI file

    If you don't have `.gitlab-ci.yml` yet:

    1. Create file `.gitlab-ci.yml` in the repository root
    2. Copy this code:

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

    3. Commit and push the file

    ### Option B: Add to existing CI

    If you already have `.gitlab-ci.yml`:

    1. Add `review` to the `stages` list (if you need a separate stage)
    2. Add this job:

    ```yaml
    ai-review:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      stage: review  # or test, or another existing stage
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

## Step 4: Check the Result

Now AI Review will run automatically on:

| Platform | Event |
|----------|-------|
| **GitHub** | PR creation, new commits in PR, reopening PR |
| **GitLab** | MR creation, new commits in MR |

### What You'll See

After the CI job completes, the PR/MR will have:

- **Inline comments** — attached to specific code lines
- **"Apply suggestion" button** — for quick fixes (GitHub)
- **Summary comment** — general overview with metrics

Each comment contains:

- :red_circle: / :yellow_circle: / :blue_circle: Severity badge
- Problem description
- Fix suggestion
- Collapsible "Why does this matter?" section

---

## Troubleshooting

### Review not appearing?

Check the checklist:

- [ ] Is `GOOGLE_API_KEY` added as a secret?
- [ ] Is `github_token` passed explicitly? (for GitHub)
- [ ] Did the CI job complete successfully? (check logs)
- [ ] For GitHub: do you have `permissions: pull-requests: write`?
- [ ] For fork PRs: secrets are not available — this is expected behavior

### Logs show `--help`?

This means the CLI didn't receive the required parameters. Check:

- Is `github_token` / `GITLAB_TOKEN` passed explicitly
- Is the YAML format correct (indentation!)

### Rate limit?

Gemini free tier: 15 requests per minute. Wait a minute and try again.

:point_right: [All issues and solutions →](troubleshooting.md)

---

## What's Next?

| Task | Document |
|------|----------|
| Configure response language | [Configuration](configuration.md) |
| Advanced GitHub settings | [GitHub Guide](github.md) |
| Advanced GitLab settings | [GitLab Guide](gitlab.md) |
| Workflow examples | [Examples](examples/index.md) |
