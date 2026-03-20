# CI/CD macOS Testing Guide

This guide explains how to test Ragtime installation on macOS in CI/CD pipelines using GitHub Actions.

**See also:** [Windows Testing Guide](ci-cd-windows.md) | [Linux Testing Guide](ci-cd-linux.md) | [Complete Workflow Example](../../.github/workflows/test-install.yml)

## Why Test on macOS?

- **Homebrew interactions**: Ensure the installer works alongside Homebrew
- **macOS-specific paths**: `/tmp` resolves to `/private/tmp`, different PATH behavior
- **ARM64 vs Intel**: Test both Apple Silicon (M1/M2) and Intel architectures
- **System Integrity Protection (SIP)**: macOS security features can affect installation
- **Bash version**: macOS ships with older bash by default

## GitHub Actions Setup

### macOS Installer Testing (Intel)

Add this job to your `.github/workflows/ci.yml`:

```yaml
macos-install-intel:
  runs-on: macos-12
  name: "Test install.sh (macOS Intel)"
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Run bash installer
      shell: bash
      run: |
        bash <(curl -fsSL ${{ github.server_url }}/${{ github.repository }}/raw/${{ github.ref_name }}/install.sh)
    
    - name: Verify installation
      shell: bash
      run: |
        ragtime --version
        proto --version
        moon --version
        uv --version
        just --version
```

### macOS Installer Testing (Apple Silicon)

```yaml
macos-install-arm64:
  runs-on: macos-14
  name: "Test install.sh (macOS Apple Silicon)"
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Run bash installer
      shell: bash
      run: |
        bash <(curl -fsSL ${{ github.server_url }}/${{ github.repository }}/raw/${{ github.ref_name }}/install.sh)
    
    - name: Verify installation
      shell: bash
      run: |
        ragtime --version
        proto --version
        moon --version
        uv --version
        just --version
```

### Testing Both macOS Architectures

Use a matrix strategy to test both Intel and Apple Silicon:

```yaml
macos-multi-arch:
  strategy:
    matrix:
      runner:
        - macos-12  # Intel
        - macos-14  # Apple Silicon (M-series)
  
  runs-on: ${{ matrix.runner }}
  name: "Test install.sh (${{ matrix.runner }})"
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Run bash installer
      shell: bash
      run: |
        bash <(curl -fsSL ${{ github.server_url }}/${{ github.repository }}/raw/${{ github.ref_name }}/install.sh)
    
    - name: Verify installation
      shell: bash
      run: |
        ragtime --version
        proto --version
        moon --version
        uv --version
        just --version
        
    - name: Show architecture
      shell: bash
      run: |
        echo "System architecture:"
        uname -m
        uname -s
```

### Testing Just Commands on macOS

```yaml
macos-justfile-testing:
  runs-on: macos-latest
  name: "Test just recipes (macOS)"
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Install tools
      shell: bash
      run: |
        bash <(curl -fsSL ${{ github.server_url }}/${{ github.repository }}/raw/${{ github.ref_name }}/install.sh)
    
    - name: Verify justfile works
      shell: bash
      run: |
        just --list
        just format-check
        just lint
```

### Testing with Homebrew Interference

To ensure the installer works even when Homebrew tools are installed:

```yaml
macos-homebrew-coexistence:
  runs-on: macos-latest
  name: "Test install.sh with Homebrew installed"
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Verify Homebrew is present
      shell: bash
      run: |
        which brew
        brew --version
    
    - name: Run bash installer
      shell: bash
      run: |
        bash <(curl -fsSL ${{ github.server_url }}/${{ github.repository }}/raw/${{ github.ref_name }}/install.sh)
    
    - name: Verify both proto and Homebrew tools work
      shell: bash
      run: |
        ragtime --version
        proto --version
        # Verify Homebrew tools still work
        brew --version
```

### Testing with Different Shell Configurations

```yaml
macos-shell-variants:
  strategy:
    matrix:
      shell:
        - bash
        - sh
        - zsh
  
  runs-on: macos-latest
  name: "Test install.sh with ${{ matrix.shell }}"
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Run installer with ${{ matrix.shell }}
      shell: ${{ matrix.shell }}
      run: |
        # Note: zsh requires different syntax for process substitution
        if [ "${{ matrix.shell }}" = "zsh" ]; then
          bash <(curl -fsSL ${{ github.server_url }}/${{ github.repository }}/raw/${{ github.ref_name }}/install.sh)
        else
          bash <(curl -fsSL ${{ github.server_url }}/${{ github.repository }}/raw/${{ github.ref_name }}/install.sh)
        fi
    
    - name: Verify installation
      shell: ${{ matrix.shell }}
      run: |
        ragtime --version
        proto --version
```

### Testing Behind Simulated Proxy

```yaml
macos-proxy-simulation:
  runs-on: macos-latest
  name: "Test install.sh with simulated proxy"
  
  env:
    HTTP_PROXY: "http://proxy.example.com:8080"
    HTTPS_PROXY: "http://proxy.example.com:8080"
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Run installer with proxy env vars
      shell: bash
      run: |
        # The installer should detect proxy and configure .prototools
        bash <(curl -fsSL ${{ github.server_url }}/${{ github.repository }}/raw/${{ github.ref_name }}/install.sh)
    
    - name: Verify .prototools was created with proxy config
      shell: bash
      run: |
        # Note: /tmp on macOS resolves to /private/tmp
        if [ -f ~/.proto/.prototools ]; then
          echo "✓ .prototools created successfully"
          cat ~/.proto/.prototools
        else
          echo "✗ .prototools not found"
          exit 1
        fi
```

### Testing PATH Persistence

Verify that the installer correctly configures shell profiles:

```yaml
macos-path-persistence:
  runs-on: macos-latest
  name: "Test install.sh PATH persistence"
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Run installer
      shell: bash
      run: |
        bash <(curl -fsSL ${{ github.server_url }}/${{ github.repository }}/raw/${{ github.ref_name }}/install.sh)
    
    - name: Verify shell profile was updated
      shell: bash
      run: |
        # Check if proto paths were added to shell profile
        PROFILE="${HOME}/.zshrc"  # or .bash_profile for bash
        if [ -f "$PROFILE" ]; then
          if grep -q "proto" "$PROFILE"; then
            echo "✓ Proto paths added to $PROFILE"
            grep "proto" "$PROFILE"
          else
            echo "✗ Proto paths not found in $PROFILE"
            exit 1
          fi
        fi
    
    - name: Verify tools work in new shell instance
      shell: bash
      run: |
        # Source the profile and verify tools are available
        source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null
        ragtime --version
        proto --version
```

## macOS-Specific Issues

### /tmp Path Resolution

On macOS, `/tmp` is actually a symlink to `/private/tmp`. The installer handles this, but be aware:

```bash
# macOS path normalization
ls -la /tmp         # Shows /private/tmp
readlink /tmp       # Shows ../../private/tmp
```

### Bash Version

macOS ships with Bash 3.2 (from 2007). Some scripts require Bash 4+:

```bash
# Check bash version
bash --version

# If needed, Homebrew can provide newer bash
brew install bash
```

### System Integrity Protection (SIP)

SIP may prevent modification of certain system directories. Proto installs to `~/.proto` which is safe.

### Xcode Command Line Tools

Some tools may require Xcode CLT. The installer handles this:

```bash
# If needed, users can install CLT
xcode-select --install
```

## Best Practices

✅ **Test multiple architectures** — Use matrix for Intel and Apple Silicon  
✅ **Test with Homebrew** — Ensure compatibility with macOS package manager  
✅ **Test multiple shells** — Try bash, sh, and zsh  
✅ **Test PATH persistence** — Verify shell profiles are updated correctly  
✅ **Test proxy scenarios** — Set env vars to simulate corporate networks  
✅ **Test just commands** — Ensure recipes work after installation  

## References

- [GitHub Actions: macOS Runners](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners)
- [Proto: macOS Installation](https://moonrepo.dev/docs/proto/install)
- [Homebrew Documentation](https://brew.sh/)
- [macOS System Integrity Protection](https://support.apple.com/en-us/HT204899)
