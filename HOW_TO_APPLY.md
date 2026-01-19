# 🔄 How to Apply File Updates

**Quick guide to replace files in your repository**

---

## 📦 Files to Replace

You have 3 updated files in `updated-files/` folder:

1. **README.md** - Updated with `uv` instructions
2. **GITHUB_SETUP.md** - Updated with `uv` workflow
3. **Makefile** - NEW file with development shortcuts

---

## 🚀 Quick Update (3 commands)

```bash
# 1. Go to your repository
cd ai-code-reviewer

# 2. Copy updated files
cp /path/to/updated-files/README.md .
cp /path/to/updated-files/GITHUB_SETUP.md .
cp /path/to/updated-files/Makefile .

# 3. Commit changes
git add README.md GITHUB_SETUP.md Makefile
git commit -m "docs: update documentation to use uv instead of pip

- README: Replace pip commands with uv
- GITHUB_SETUP: Add uv-based workflow
- Makefile: Add development shortcuts"
git push
```

---

## 📋 Detailed Steps

### Step 1: Backup Current Files (Optional)

```bash
cd ai-code-reviewer

# Create backup
mkdir -p .backups
cp README.md .backups/README.md.backup
cp GITHUB_SETUP.md .backups/GITHUB_SETUP.md.backup
```

### Step 2: Download Updated Files

If files are in archive:
```bash
# Extract to temporary location
tar -xzf updated-files.tar.gz -C /tmp
```

### Step 3: Replace Files

```bash
# Replace one by one
cp /tmp/updated-files/README.md .
cp /tmp/updated-files/GITHUB_SETUP.md .
cp /tmp/updated-files/Makefile .

# Verify changes
git diff README.md        # Check what changed
git diff GITHUB_SETUP.md
git status                # See all changes
```

### Step 4: Test Makefile

```bash
# Test new Makefile
make help     # Should show all commands

# Try a command
make quick    # Should run ruff + mypy
```

### Step 5: Commit & Push

```bash
# Add files
git add README.md GITHUB_SETUP.md Makefile

# Commit
git commit -m "docs: update documentation to use uv

- Replace pip with uv in all setup instructions
- Add Makefile for development shortcuts
- Update GITHUB_SETUP with uv workflow"

# Push
git push origin main
```

---

## 🔍 What Changed?

### README.md

**Before:**
```bash
pip install -e ".[dev]"
pre-commit install
```

**After:**
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
uv run pre-commit install
```

**Also added:**
- Makefile commands
- uv acknowledgment
- Better setup instructions

---

### GITHUB_SETUP.md

**Before:**
```bash
pip install pre-commit
pre-commit install
```

**After:**
```bash
uv pip install -e ".[dev]"
uv run pre-commit install
```

**Also added:**
- Complete uv setup workflow
- Makefile usage examples
- Pre-commit troubleshooting

---

### Makefile (NEW)

Adds development shortcuts:

```bash
make help      # Show all commands
make setup     # Complete setup
make install   # Install dependencies
make test      # Run tests
make lint      # Check code quality
make format    # Format code
make quick     # Quick check before commit
make docs      # Serve documentation
```

---

## ✅ Verification

After applying updates, verify:

```bash
# 1. Check README mentions uv
grep "uv venv" README.md
# Should output: uv venv

# 2. Check Makefile exists and works
make help
# Should show list of commands

# 3. Check git status
git status
# Should show 3 modified/new files

# 4. Check no syntax errors
cat Makefile | head -20  # Should look good
```

---

## 🎯 Quick Replace Script

Create this script to automate:

```bash
#!/bin/bash
# save as: apply-updates.sh

UPDATED_FILES_DIR="/path/to/updated-files"
REPO_DIR="/path/to/ai-code-reviewer"

cd "$REPO_DIR"

echo "Applying file updates..."

# Copy files
cp "$UPDATED_FILES_DIR/README.md" .
cp "$UPDATED_FILES_DIR/GITHUB_SETUP.md" .
cp "$UPDATED_FILES_DIR/Makefile" .

echo "Files copied. Changes:"
git status --short

echo ""
echo "Review changes with: git diff"
echo "Commit with: git commit -am 'docs: update to use uv'"
```

Make it executable and run:
```bash
chmod +x apply-updates.sh
./apply-updates.sh
```

---

## 🔄 If Using Downloaded Archive

If you extracted from `ai-code-reviewer.tar.gz`:

```bash
# Extract archive
tar -xzf ai-code-reviewer.tar.gz

# Your working repo
cd /path/to/your/ai-code-reviewer

# Copy from extracted
cp ../ai-code-reviewer/README.md .
cp ../ai-code-reviewer/GITHUB_SETUP.md .
cp ../ai-code-reviewer/Makefile .

# Commit
git add .
git commit -m "docs: update to use uv"
git push
```

---

## 🐛 Troubleshooting

### "File not found"
```bash
# Check you're in right directory
pwd
ls README.md  # Should exist

# Check source path
ls /path/to/updated-files/README.md
```

### "Permission denied"
```bash
# Make files readable
chmod 644 README.md GITHUB_SETUP.md Makefile
```

### Makefile not working
```bash
# Check Makefile has tabs (not spaces)
cat -A Makefile | head  # Should show ^I (tabs)

# If spaces, convert:
# Use proper editor or sed to convert
```

### Git shows weird diff
```bash
# Maybe line endings changed
git config core.autocrlf input  # Unix line endings
git add -u
git commit --amend
```

---

## 📝 Alternative: Manual Edit

If you prefer to edit manually:

### README.md Changes:
1. Find all `pip install` → Replace with `uv pip install`
2. Find all `pre-commit install` → Replace with `uv run pre-commit install`
3. Add `uv venv` and activation before install commands
4. Add Makefile section in Development

### GITHUB_SETUP.md Changes:
1. Same as README
2. Add Makefile usage examples
3. Update troubleshooting section

### Add Makefile:
1. Copy entire content from `updated-files/Makefile`
2. Ensure it uses TABS not spaces
3. Test with `make help`

---

## ✅ Completion Checklist

After applying updates:

- [ ] Files replaced
- [ ] `make help` works
- [ ] `make quick` runs successfully
- [ ] Changes committed
- [ ] Pushed to GitHub
- [ ] README displays correctly on GitHub
- [ ] Documentation mentions uv
- [ ] Makefile in repository root

---

## 🎉 Done!

Your repository now has:
- ✅ Consistent `uv` usage
- ✅ Makefile for productivity
- ✅ Better setup instructions

**Next:** Start developing with `make quick` before each commit!
