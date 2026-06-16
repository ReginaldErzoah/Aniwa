## First Time Contributor Guide

### Step 1: Fork & Clone

```bash
# Click "Fork" button on GitHub (top right)

# Then clone YOUR fork
git clone https://github.com/YOUR_USERNAME/Aniwa.git
cd Aniwa

# Add original repo as "upstream"
git remote add upstream https://github.com/ReginaldErzoah/Aniwa.git
```

---

### Step 2: Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate
pip install -e .[dev]
```

---

### Step 3: Create Branch

```bash
git checkout -b your-branch-name
```

---

### Step 4: Make Changes & Push

```bash
git add .
git commit -m "type: description"
git push origin your-branch-name
```

---

### Step 5: Create Pull Request

Go to GitHub → Click "Compare & pull request"

---

## How to Rebase (When Your Branch is Behind)

### Check if you're behind:
```bash
git fetch upstream
git status
# If it says "behind", run the commands below
```

### Fix it:
```bash
git fetch upstream
git rebase upstream/main
git push origin your-branch-name --force
```

### If conflicts happen:
```bash
# Fix the conflicting file manually, then:
git add .
git rebase --continue
git push origin your-branch-name --force
```

### Stuck?
```bash
git rebase --abort   # Go back to before rebase
# Ask for help!
```

---

## Summary

| Step | Command |
|------|---------|
| Fork | Click button on GitHub |
| Clone | `git clone https://github.com/YOU/Aniwa.git` |
| Add upstream | `git remote add upstream https://github.com/ReginaldErzoah/Aniwa.git` |
| Create branch | `git checkout -b my-branch` |
| Push | `git push origin my-branch` |
| Rebase | `git fetch upstream && git rebase upstream/main && git push --force` |

