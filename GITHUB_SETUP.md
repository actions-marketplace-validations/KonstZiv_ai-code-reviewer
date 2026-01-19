# GitHub Repository Setup Guide

Complete instructions for setting up your AI Code Reviewer project on GitHub.

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Extract Project

```bash
# Extract the archive
tar -xzf ai-code-reviewer.tar.gz
cd ai-code-reviewer

# Verify structure
ls -la
```

### Step 2: Initialize Git

```bash
# Initialize git repository
git init

# Add all files
git add .

# Initial commit
git commit -m "feat: initial project structure with multi-LLM support

- Complete project structure
- Multi-LLM router (Anthropic, OpenAI, Google, DeepSeek)
- 3 deployment scenarios (free, small team, enterprise)
- MkDocs documentation
- GitHub Actions workflows
- AI-friendly task tracking"
```

### Step 3: Create GitHub Repository

#### Option A: Using GitHub Web UI (Recommended)

1. Go to https://github.com/new
2. **Repository name:** `ai-code-reviewer`
3. **Description:** `AI-powered code review agent for CI/CD pipelines`
4. **Visibility:** 
   - ✅ **Public** (unlimited CI minutes)
   - OR Private (2000 minutes/month free)
5. **Do NOT initialize with:**
   - ❌ README (we have one)
   - ❌ .gitignore (we have one)
   - ❌ License (we have one)
6. Click **Create repository**

#### Option B: Using GitHub CLI

```bash
# Install GitHub CLI (if not installed)
# macOS: brew install gh
# Linux: https://github.com/cli/cli#installation

# Login
gh auth login

# Create repository
gh repo create ai-code-reviewer \
  --public \
  --description "AI-powered code review agent for CI/CD pipelines" \
  --source=. \
  --push
```

### Step 4: Push to GitHub

If you used Web UI (Option A):

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/ai-code-reviewer.git

# Rename branch to main (if needed)
git branch -M main

# Push
git push -u origin main
```

If you used CLI (Option B), you're already done! 🎉

---

## 🔧 Post-Setup Configuration

### Enable GitHub Pages (for docs)

1. Go to repository **Settings** → **Pages**
2. **Source:** Deploy from a branch
3. **Branch:** `gh-pages` (will be created by Actions)
4. Click **Save**

Docs will be available at: `https://YOUR_USERNAME.github.io/ai-code-reviewer/`

### Add Repository Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add at least one LLM provider:

| Name | Value | Where to get |
|------|-------|--------------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | https://console.anthropic.com/ |
| `GOOGLE_API_KEY` | `AI...` | https://makersuite.google.com/app/apikey |
| `OPENAI_API_KEY` | `sk-...` | https://platform.openai.com/api-keys |
| `DEEPSEEK_API_KEY` | `sk-...` | https://platform.deepseek.com/ |

**Recommended for start:** `GOOGLE_API_KEY` (free tier)

### Enable GitHub Actions

1. Go to **Actions** tab
2. Click **I understand my workflows, go ahead and enable them**

### Protect Main Branch (Optional)

1. **Settings** → **Branches** → **Add rule**
2. **Branch name pattern:** `main`
3. Check:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass
     - Search and add: `test (3.11)`, `test (3.12)`
   - ✅ Require conversation resolution before merging
4. **Create**

---

## 📊 Repository Setup Checklist

- [ ] Repository created on GitHub
- [ ] Code pushed to `main` branch
- [ ] GitHub Pages enabled
- [ ] At least one API key added to Secrets
- [ ] GitHub Actions enabled
- [ ] Branch protection rules set (optional)
- [ ] README.md displays correctly on GitHub
- [ ] Documentation building (check Actions tab)

---

## 🎯 First Pull Request

### Create Development Branch

```bash
# Create and switch to new branch
git checkout -b feature/multi-llm-router

# Start implementing
# (See CURRENT_TASK/TASK_DESCRIPTION.md)
vim src/ai_reviewer/llm/base.py

# Commit changes
git add .
git commit -m "feat(llm): implement base abstractions for multi-LLM router"

# Push
git push -u origin feature/multi-llm-router
```

### Create PR

```bash
# Using GitHub CLI
gh pr create \
  --title "feat(llm): Multi-LLM Router Implementation" \
  --body "Implements base abstractions and router logic for multi-LLM support. See CURRENT_TASK/TASK_DESCRIPTION.md for details."

# Or manually on GitHub
# Go to repository → Pull requests → New pull request
```

### Watch AI Review in Action

Once you have the full system working, AI will:
1. Detect PR creation
2. Run analysis
3. Post review comments
4. Update PR status

---

## 📁 Repository Structure on GitHub

```
your-username/ai-code-reviewer
├── .github/
│   ├── workflows/           # CI/CD workflows
│   ├── ISSUE_TEMPLATE/      # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
├── src/ai_reviewer/         # Source code
├── tests/                   # Tests
├── docs/                    # Documentation
├── GENERAL_PROJECT_DESCRIPTION/
├── CURRENT_TASK/
└── ... (all project files)
```

---

## 🔒 Security Settings

### Recommended Settings

1. **Security** → **Code security and analysis**
   - ✅ Dependabot alerts
   - ✅ Dependabot security updates
   - ✅ Secret scanning

2. **Settings** → **Actions** → **General**
   - Workflow permissions: **Read and write permissions**
   - ✅ Allow GitHub Actions to create and approve pull requests

---

## 🌐 Making Repository Public vs Private

### Public Repository (Recommended for open source)

**Pros:**
- ✅ Unlimited CI minutes
- ✅ Free GitHub Pages
- ✅ Community contributions
- ✅ Portfolio/resume project

**Cons:**
- ❌ Code visible to everyone
- ❌ Secrets must be carefully managed

### Private Repository

**Pros:**
- ✅ Code hidden from public
- ✅ Control over access

**Cons:**
- ❌ 2000 CI minutes/month limit
- ❌ GitHub Pages requires paid plan (or use Netlify/Vercel)

**Recommendation:** Start public unless you have proprietary code.

---

## 🎨 Repository Customization

### Add Topics

**Settings** → **About** → **Topics**

Add tags like:
- `code-review`
- `ai`
- `llm`
- `github-actions`
- `python`
- `langchain`
- `cicd`

### Add Social Image

**Settings** → **About** → **Upload image**

Create a banner with project logo/name.

### Update Description

**Settings** → **About** → **Description**

Short tagline: `AI-powered code review agent for CI/CD pipelines`

Add website: `https://YOUR_USERNAME.github.io/ai-code-reviewer/`

---

## 📈 Next Steps After Setup

1. **Read current task:**
   ```bash
   cat CURRENT_TASK/TASK_DESCRIPTION.md
   ```

2. **Start development:**
   ```bash
   # Create feature branch
   git checkout -b feature/multi-llm-router
   
   # Implement
   vim src/ai_reviewer/llm/base.py
   
   # Test
   pytest
   
   # Commit & push
   git add . && git commit -m "feat(llm): ..."
   git push -u origin feature/multi-llm-router
   ```

3. **Create first PR**

4. **Watch CI/CD run**

---

## 🐛 Troubleshooting

### Can't push to GitHub?

```bash
# Check remote
git remote -v

# If wrong, remove and re-add
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/ai-code-reviewer.git

# Or use SSH
git remote add origin git@github.com:YOUR_USERNAME/ai-code-reviewer.git
```

### GitHub Actions not running?

1. Check **Actions** tab
2. Ensure workflows are enabled
3. Check branch protection rules aren't blocking

### Documentation not building?

1. Check **Actions** tab → **Documentation** workflow
2. Verify `mkdocs.yml` is valid
3. Check Python version in workflow

---

## 💬 Get Help

- 📖 [Full Documentation](https://ai-code-reviewer.readthedocs.io)
- 🐛 [Open an Issue](https://github.com/YOUR_USERNAME/ai-code-reviewer/issues)
- 💬 [Discussions](https://github.com/YOUR_USERNAME/ai-code-reviewer/discussions)

---

## ✅ You're All Set!

Your repository is ready for development. Start coding! 🚀

**Next:** Read `CURRENT_TASK/TASK_DESCRIPTION.md` and start implementing the Multi-LLM Router.
