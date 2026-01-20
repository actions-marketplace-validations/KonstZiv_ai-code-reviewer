# Sprint 1 Task - How to Apply

**Quick guide to start Sprint 1**

---

## 📦 Files to Copy

Copy these to your repository:

```bash
# Go to your repo
cd ai-code-reviewer

# Copy task description
cp /path/to/TASK_DESCRIPTION.md CURRENT_TASK/

# Copy progress canvas
cp /path/to/PROCESS_TASK.md CURRENT_TASK/

# Commit
git add CURRENT_TASK/
git commit -m "docs: add Sprint 1 - MVP Code Reviewer task"
git push
```

---

## 🎯 Sprint 1 Overview

**Goal:** Build minimal working code reviewer that verifies entire toolchain

**What you'll build:**
- Simple AI reviewer using Google Gemini (free)
- Complete CI/CD pipeline
- Multi-language documentation (6 languages)
- First PyPI release (v0.1.0)

**What you'll verify:**
- ✅ All dev tools (ruff, mypy, pytest, pre-commit)
- ✅ GitHub Actions CI/CD
- ✅ Documentation deployment
- ✅ PyPI publishing
- ✅ LLM integration

---

## 📋 Sprint Structure

**8 Tasks (ordered):**

1. **Environment Setup** (1-2h) - Verify all tools work
2. **Core Models** (2-3h) - Define data structures
3. **Configuration** (1-2h) - Environment management
4. **GitHub Integration** (3-4h) - Fetch PR data
5. **Gemini Integration** (3-4h) - AI analysis
6. **Review Logic** (2-3h) - Main workflow
7. **CLI & GitHub Action** (2h) - User interface
8. **Multi-Lang Docs** (4-5h) - 6 languages

**Total: ~20-28 hours work**

---

## 🚀 How to Start

### Step 1: Read the Task
```bash
cd CURRENT_TASK
cat TASK_DESCRIPTION.md  # Full task description
```

### Step 2: Open Progress Canvas
```bash
cat PROCESS_TASK.md  # Track your progress here
```

### Step 3: Start with Task 1
```bash
# Follow Task 1 checklist in PROCESS_TASK.md
# Update checkboxes as you complete steps
```

### Step 4: Work Through Tasks
- Complete tasks in order (1→8)
- Update PROCESS_TASK.md as you go
- Run tests after each task
- Commit frequently

---

## 💡 For AI Assistant (Claude)

**When starting work session:**

1. Read both files:
   ```
   CURRENT_TASK/TASK_DESCRIPTION.md
   CURRENT_TASK/PROCESS_TASK.md
   ```

2. Find current task:
   - Look for last completed checkbox
   - Start next incomplete task

3. Before implementing:
   - Read task requirements
   - Ask clarifying questions
   - Propose approach
   - Wait for approval

4. While working:
   - Update PROCESS_TASK.md checkboxes
   - Add notes about decisions
   - Document blockers
   - Run tests frequently

5. After completing task:
   - Mark task as ✅ Done
   - Run full test suite
   - Update metrics
   - Move to next task

---

## 📝 For Human Developer

**Review Process:**

1. **Before AI starts task:**
   - Review task requirements
   - Clarify any unclear points
   - Approve approach

2. **During implementation:**
   - Monitor progress in PROCESS_TASK.md
   - Review code incrementally
   - Test manually when ready

3. **After task completion:**
   - Run full test suite
   - Test manually if applicable
   - Review code quality
   - Approve or request changes

4. **Sprint management:**
   - Update daily standup section
   - Log decisions and issues
   - Track blockers

---

## 🎓 Expected Outcomes

After Sprint 1, you'll have:

**Functional:**
- ✅ Working AI code reviewer
- ✅ Posted reviews on GitHub PRs
- ✅ Documentation in 6 languages

**Technical:**
- ✅ Complete Python project
- ✅ 80%+ test coverage
- ✅ All CI/CD workflows green
- ✅ Published to PyPI (v0.1.0)

**Knowledge:**
- ✅ Verified entire dev workflow
- ✅ Understand all tooling
- ✅ LLM integration basics
- ✅ Multi-language docs

---

## 📊 Progress Tracking

**In PROCESS_TASK.md, update:**

- [ ] Task checkboxes as you complete steps
- [ ] Daily standup section
- [ ] Decision log for important choices
- [ ] Issues & solutions as they occur
- [ ] Learnings as you discover them
- [ ] Metrics at sprint end

**This creates a complete record for future reference!**

---

## ⚠️ Important Notes

### Keep It Simple
- This is MVP - simplest working version
- Don't add extra features
- Focus on verifying toolchain
- Complexity comes in later sprints

### Test Everything
- Run tests after each component
- Don't skip testing
- Coverage is important
- Manual testing required

### Document As You Go
- Update PROCESS_TASK.md frequently
- Document decisions
- Note blockers immediately
- Keep standup current

### Ask Questions
- If unclear, ask before implementing
- Better to clarify than redo
- Document answers in decision log

---

## 🎯 Success Criteria

Sprint 1 is **DONE** when:

1. ✅ All 8 tasks completed
2. ✅ All tests pass (≥80% coverage)
3. ✅ Manual PR test successful
4. ✅ Documentation in 6 languages
5. ✅ Published to PyPI as v0.1.0
6. ✅ All CI/CD workflows green
7. ✅ PROCESS_TASK.md fully updated

---

## 🚀 Let's Go!

```bash
# Start Sprint 1
cd CURRENT_TASK
vim PROCESS_TASK.md  # Update "Sprint Start" date

# Begin Task 1
# Follow checklist in PROCESS_TASK.md
```

**Good luck! 🎉**

---

## 📞 Support

If stuck:
1. Check TASK_DESCRIPTION.md for details
2. Review relevant docs
3. Ask clarifying questions
4. Document the issue in PROCESS_TASK.md

Remember: This sprint is about learning the workflow as much as building the feature!
