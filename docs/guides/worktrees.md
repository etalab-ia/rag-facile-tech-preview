# Working with Git Worktrees

This repository uses a **bare repo + worktree** setup to support parallel development — multiple branches can be checked out simultaneously, each in its own directory, without interfering with each other.

---

## Repository Layout

```
ragtime/
├── .bare/              # Git data (bare clone — not a working directory)
├── .git                # Pointer file → .bare (makes standard git tools work)
├── .config/
│   └── wt.toml         # Project-level worktrunk hooks (committed to repo)
├── .worktreeinclude    # Controls which gitignored files are copied to new worktrees
├── .worktrees/         # Feature worktrees (hidden, managed by worktrunk)
│   ├── feat-my-feature/
│   └── fix-some-bug/
└── main/               # Main branch — source of truth for shared files
    ├── .env            # Secrets — canonical copy, never commit
    ├── .letta/         # Letta Code settings
    └── .ragtime/    # Agent memory & config
```

`main/` is a regular checkout of the `main` branch. **Never commit work directly to it** — it's a stable reference point. Create a worktree for every piece of work.

---

## Prerequisites

### 1. Worktrunk

Install [worktrunk](https://worktrunk.dev) — a CLI that makes worktrees as easy as branches:

```bash
# macOS (Homebrew)
brew install worktrunk && wt config shell install
```

For Linux, Windows, or other platforms, see [worktrunk.dev](https://worktrunk.dev) for installation options.

Shell integration is required for `wt switch` to change directories automatically.

### 2. Worktrunk user config

Configure worktrunk to place new worktrees in the hidden `.worktrees/` directory:

```toml
# ~/.config/worktrunk/config.toml
[projects."github.com/etalab-ia/ragtime"]
worktree-path = "../.worktrees/{{ branch | sanitize }}"
```

Create the file if it doesn't exist: `wt config create`, then add the `[projects]` section above.

---

## Initial Clone

```bash
# 1. Create the workspace directory
mkdir ~/projects/ragtime && cd ~/projects/ragtime

# 2. Bare clone — --single-branch avoids creating local tracking branches for
#    every remote branch
git clone --bare --single-branch git@github.com:etalab-ia/ragtime.git .bare

# 3. Create the .git pointer file
echo "gitdir: ./.bare" > .git

# 4. Configure fetch so remote branches are visible (needed after --single-branch)
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

# 5. Portable paths (workspace can be moved without breaking)
git config worktree.useRelativePaths true

# 6. Fetch all remote branches as remotes (not local branches)
git fetch --all

# 7. Create the main worktree
git worktree add main main
git -C main branch --set-upstream-to=origin/main main

# 8. Install Python dependencies
cd main && uv sync

# 9. Create your .env from the example and fill in your API key
cp .env.example .env
```

---

## Daily Workflow

### Start work on a new branch

```bash
wt switch --create feat/my-feature
```

Worktrunk automatically:
1. Creates the branch and worktree at `.worktrees/feat-my-feature/`
2. Runs `uv sync` (post-create hook)
3. Copies gitignored files from `main/` — `.env`, `.letta/`, `.ragtime/` (post-start hook)

No manual dependency installation or `.env` copying needed.

### List all worktrees

```bash
wt list
```

### Switch between worktrees

```bash
wt switch feat/my-feature
wt switch -     # previous worktree (like cd -)
wt switch ^     # main worktree
```

### Clean up after a PR is merged

```bash
wt remove                       # from inside the worktree
wt remove feat/my-feature       # from anywhere
wt step prune                   # remove all merged worktrees at once
```

### Update main

```bash
cd ~/projects/ragtime/main && git pull
```

---

## How `.env` and Other Secrets Are Shared

When a new worktree is created, `wt step copy-ignored` (configured as a post-start hook in `.config/wt.toml`) copies gitignored files from `main/` into the new worktree.

`.config/wt.toml` is a **project-level** config committed to the repo, distinct from your personal `~/.config/worktrunk/config.toml`. Run `wt hook show` to inspect active hooks.

The `.worktreeinclude` file in the repo root controls what gets copied:

```
# Secrets
.env

# Letta Code settings
.letta

# Agent memory & config
.ragtime
```

**Edit `.env` in `main/`** — it's the canonical source. Each new worktree gets a fresh copy on creation.

---

## Why bare repo?

A standard `git clone` gives you one working directory. Switching branches means stashing, switching, and losing context. The bare repo pattern gives each branch its own directory — `feat/auth` and `fix/bug` coexist side by side with no interference.

This is especially useful when running multiple AI coding agents in parallel on different features simultaneously, or when you want to keep a stable reference copy of `main` running while actively developing on a feature branch.
