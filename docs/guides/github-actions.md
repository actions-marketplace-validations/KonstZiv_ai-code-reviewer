# GitHub Actions Integration

Complete guide for using AI Code Reviewer with GitHub Actions.

---

## 🚀 Quick Start (1 Minute)

### 1. Add API Key to Repository Secrets

Go to: `Settings → Secrets and variables → Actions → New repository secret`

Add at least one:
- `ANTHROPIC_API_KEY` - Claude (recommended)
- `GOOGLE_API_KEY` - Gemini (free tier)
- `OPENAI_API_KEY` - GPT

### 2. Create Workflow File

`.github/workflows/ai-code-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for context
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install AI Code Reviewer
        run: |
          pip install ai-code-reviewer
      
      - name: Run Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          ai-review github \
            --pr-number ${{ github.event.pull_request.number }} \
            --repo ${{ github.repository }}
```

### 3. Create Pull Request

That's it! Next PR will get AI review automatically.

---

## 📋 Configuration Options

### Basic Configuration

Create `.ai-reviewer.yml` in your repo:

```yaml
llm:
  providers:
    - anthropic
  
  anthropic:
    models:
      simple: claude-3-5-haiku-20241022
      medium: claude-3-5-sonnet-20241022
      complex: claude-3-5-sonnet-20241022

review:
  analysis_depth: normal
  enabled_agents:
    - security
    - architecture
    - qa
  
  can_auto_approve: false
```

### Use Configuration in Workflow

```yaml
- name: Run Review
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    ai-review github \
      --pr-number ${{ github.event.pull_request.number }} \
      --repo ${{ github.repository }} \
      --config .ai-reviewer.yml
```

---

## 🎯 Deployment Scenarios

### Scenario 1: Free Tier (Gemini)

**Cost:** $0  
**Reviews/month:** ~100

```yaml
name: AI Code Review (Free)

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install
        run: pip install ai-code-reviewer
      
      - name: Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          ai-review github \
            --pr-number ${{ github.event.pull_request.number }} \
            --repo ${{ github.repository }} \
            --config config/deployment/quick-start/config.yml
```

**Setup:**
1. Get free API key: https://makersuite.google.com/app/apikey
2. Add to repo secrets as `GOOGLE_API_KEY`
3. Commit workflow

---

### Scenario 2: Small Team (Hybrid)

**Cost:** ~$10-30/month  
**Reviews/month:** ~500

```yaml
name: AI Code Review (Hybrid)

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install
        run: pip install ai-code-reviewer
      
      - name: Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          ai-review github \
            --pr-number ${{ github.event.pull_request.number }} \
            --repo ${{ github.repository }} \
            --config config/deployment/small-team/config.yml
```

**Setup:**
1. Get API keys:
   - Anthropic: https://console.anthropic.com/
   - Google (backup): https://makersuite.google.com/
2. Add both to repo secrets
3. Commit workflow

**Cost optimization:**
- Simple tasks → Gemini (free)
- Complex tasks → Claude (paid)

---

### Scenario 3: Enterprise (Self-Hosted Runner)

**Cost:** Infrastructure + modest API  
**Reviews/month:** 2000+

#### Setup Self-Hosted Runner

1. **Create runner VM:**
   ```bash
   # Ubuntu 22.04 with GPU (optional)
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Pull models
   ollama pull llama3.1:8b
   ollama pull codellama:13b
   ```

2. **Add runner to GitHub:**
   - Go to `Settings → Actions → Runners → New self-hosted runner`
   - Follow setup instructions

3. **Create workflow:**

```yaml
name: AI Code Review (Enterprise)

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: [self-hosted, linux]
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OLLAMA_URL: http://localhost:11434
        run: |
          ai-review github \
            --pr-number ${{ github.event.pull_request.number }} \
            --repo ${{ github.repository }} \
            --config config/deployment/enterprise/config.yml
```

**Benefits:**
- 90% reviews use free local LLM
- 10% complex reviews use Claude
- Full control over infrastructure

---

## 🔒 Security Best Practices

### 1. Use Repository Secrets

Never hardcode API keys in workflow files!

```yaml
# ❌ BAD
env:
  ANTHROPIC_API_KEY: sk-ant-1234...

# ✅ GOOD
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### 2. Limit Permissions

```yaml
permissions:
  pull-requests: write  # Only what's needed
  contents: read
```

### 3. Use Dependabot

Enable Dependabot for automatic dependency updates:

`.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## 📊 Monitoring & Metrics

### View Workflow Runs

`Actions` tab → Select workflow → See runs

### Cost Tracking

Add this to your workflow:

```yaml
- name: Report Costs
  if: always()
  run: |
    cat /tmp/ai-review-costs.json || echo "No costs tracked"
```

### GitHub Status Checks

AI Code Review will post status to PR:
- ✅ Approved
- ⚠️ Changes requested
- ❌ Rejected

---

## 🐛 Troubleshooting

### Review not posting comments?

Check:
1. `GITHUB_TOKEN` has `pull-requests: write` permission
2. API key is valid
3. Workflow logs for errors

### API rate limits?

Switch provider or add fallback:

```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}  # Fallback
```

### Slow reviews?

Use shallow analysis:

```yaml
run: |
  ai-review github \
    --pr-number ${{ github.event.pull_request.number }} \
    --repo ${{ github.repository }} \
    --depth shallow
```

---

## 🔗 Next Steps

- [Configuration Reference](../configuration/index.md)
- [Cost Optimization](cost-optimization.md)
- [Adding Custom Agents](../development/adding-agents.md)

---

## 💬 Support

- 📖 [Documentation](https://ai-code-reviewer.readthedocs.io)
- 🐛 [Issues](https://github.com/your-org/ai-code-reviewer/issues)
- 💬 [Discussions](https://github.com/your-org/ai-code-reviewer/discussions)
