# Uninstalling Ragtime

This guide explains how to remove Ragtime and optionally the toolchain installed by the installer.

## Quick Uninstall

Remove the ragtime CLI:

```bash
ragtime uninstall
```

Remove the CLI **and** the entire toolchain (proto, moon, uv, just, direnv):

```bash
ragtime uninstall --all
```

Both commands show what will be removed and ask for confirmation. Use `--yes` to skip the prompt.

## What Gets Removed

With `--all`, the uninstall command removes everything the installer put on your machine:

| Component | Location | Description |
|-----------|----------|-------------|
| ragtime CLI | `~/.local/bin/ragtime` | The CLI tool itself |
| moon | `~/.proto/` | Workspace task runner |
| uv | `~/.proto/` | Python package manager |
| just | `~/.proto/` | Command runner |
| proto | `~/.proto/` | Toolchain manager (manages moon, uv, just) |
| direnv | system | Environment variable manager (Unix only) |
| Shell profile entries | `~/.zshrc`, `~/.bashrc`, etc. | PATH exports added by the installer |

On Windows, the uninstall also cleans up User PATH entries in the registry.

> **Note**: Projects you created with `ragtime setup` are **not** removed. Delete those directories yourself if you no longer need them.

## Windows

On Windows (PowerShell), the same command works:

```powershell
ragtime uninstall
```

## Manual Uninstall

If the `ragtime` command is not available, you can remove everything manually.

### Linux / macOS / WSL

```bash
# 1. Remove the CLI
uv tool uninstall ragtime-cli

# 2. Remove proto-managed tools
proto uninstall moon
proto uninstall uv
proto uninstall just

# 3. Remove proto itself
rm -rf ~/.proto

# 4. Remove direnv (optional)
brew uninstall direnv    # macOS
sudo apt remove direnv   # Ubuntu/Debian

# 5. Clean your shell profile (~/.zshrc, ~/.bashrc, etc.)
#    Remove lines marked with "# Added by Ragtime installer"
#    and any "eval $(direnv hook ...)" lines
```

Then restart your terminal.

### Windows (PowerShell)

```powershell
# 1. Remove the CLI
uv tool uninstall ragtime-cli

# 2. Remove proto-managed tools
proto uninstall moon
proto uninstall uv
proto uninstall just

# 3. Remove proto itself
Remove-Item -Recurse -Force "$env:USERPROFILE\.proto"

# 4. Clean User PATH (remove entries for .proto\bin, .proto\shims, .local\bin)
#    System > Advanced > Environment Variables > User variables > Path
```

Then open a new PowerShell window.
