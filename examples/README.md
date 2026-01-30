# AI Code Reviewer - Integration Examples

This directory contains example configurations for integrating AI Code Reviewer into your CI/CD pipelines.

## Quick Start

### GitHub Actions

1. Copy `github-workflow.yml` to `.github/workflows/ai-review.yml` in your repository
2. Add `GOOGLE_API_KEY` to your repository secrets (Settings → Secrets → Actions)
3. Create a pull request to see AI Code Review in action

### GitLab CI

1. Add `GOOGLE_API_KEY` to your CI/CD variables (Settings → CI/CD → Variables)
2. Include the template in your `.gitlab-ci.yml`:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/KonstZiv/ai-code-reviewer/main/examples/gitlab-ci.yml'
```

Or copy the job from `gitlab-ci.yml` to your pipeline.

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `LANGUAGE` | Response language (ISO 639 code) | `en` |
| `LANGUAGE_MODE` | `adaptive` (detect from PR) or `fixed` | `adaptive` |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

## Docker Usage

You can also run the reviewer directly with Docker:

```bash
# Pull the image
docker pull ghcr.io/konstziv/ai-code-reviewer:1

# Run with environment variables
docker run --rm \
  -e GITHUB_TOKEN="ghp_xxx" \
  -e GOOGLE_API_KEY="xxx" \
  -e GITHUB_REPOSITORY="owner/repo" \
  -e GITHUB_REF="refs/pull/123/merge" \
  ghcr.io/konstziv/ai-code-reviewer:1
```

## Supported Platforms

| Platform | Method | Token |
|----------|--------|-------|
| GitHub | GitHub Action | `GITHUB_TOKEN` (automatic) |
| GitLab | Docker image | Project Access Token (`GITLAB_TOKEN`) |

## Troubleshooting

### GitHub: "Resource not accessible by integration"

The default `GITHUB_TOKEN` may lack permissions. Create a Personal Access Token with `repo` scope and add it as `GH_TOKEN` secret.

### GitLab: "403 Forbidden"

Create a Project Access Token with `api` scope and add it as `GITLAB_TOKEN` variable.

### Rate Limiting

Both GitHub and GitLab have API rate limits. The reviewer automatically handles rate limiting with retries and backoff.

## Examples

### Multi-language Support

```yaml
# Respond in Ukrainian
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    language: 'uk'
    language_mode: 'fixed'
```

### Using Different Model

```yaml
# Use Gemini 1.5 Pro for more complex reviews
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    gemini_model: 'gemini-1.5-pro'
```

## Cost Estimation

The reviewer displays estimated costs in the review footer. Typical costs:

| Model | ~2000 tokens | ~10000 tokens |
|-------|--------------|---------------|
| gemini-2.5-flash | ~$0.0002 | ~$0.001 |
| gemini-1.5-pro | ~$0.005 | ~$0.025 |
