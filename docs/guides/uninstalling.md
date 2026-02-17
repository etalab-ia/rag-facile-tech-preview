# Uninstalling RAG Facile

This guide explains how to completely remove RAG Facile and the toolchain installed by the installer.

## Quick Uninstall

```bash
rag-facile uninstall
```

The command shows what will be removed and asks for confirmation. Use `--yes` to skip the prompt:

```bash
rag-facile uninstall --yes
```

## What Gets Removed

The uninstall command removes everything the installer put on your machine:

| Component | Location | Description |
|-----------|----------|-------------|
| rag-facile CLI | `~/.local/bin/rag-facile` | The CLI tool itself |
| moon | `~/.proto/` | Workspace task runner |
| uv | `~/.proto/` | Python package manager |
| just | `~/.proto/` | Command runner |
| proto | `~/.proto/` | Toolchain manager (manages moon, uv, just) |
| direnv | system | Environment variable manager (Unix only) |
| Shell profile entries | `~/.zshrc`, `~/.bashrc`, etc. | PATH exports added by the installer |

On Windows, the uninstall also cleans up User PATH entries in the registry.

> **Note**: Projects you created with `rag-facile setup` are **not** removed. Delete those directories yourself if you no longer need them.

## Windows

On Windows (PowerShell), the same command works:

```powershell
rag-facile uninstall
```

## Manual Uninstall

If the `rag-facile` command is not available, you can remove everything manually.

### Linux / macOS / WSL

```bash
# 1. Remove the CLI
uv tool uninstall rag-facile-cli

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
#    Remove lines marked with "# Added by RAG Facile installer"
#    and any "eval $(direnv hook ...)" lines
```

Then restart your terminal.

### Windows (PowerShell)

```powershell
# 1. Remove the CLI
uv tool uninstall rag-facile-cli

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
