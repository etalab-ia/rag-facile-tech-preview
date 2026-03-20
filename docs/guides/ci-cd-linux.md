# CI/CD Linux Testing Guide

This guide explains how to test Ragtime installation on Linux in CI/CD pipelines using GitHub Actions.

**See also:** [Windows Testing Guide](ci-cd-windows.md) | [macOS Testing Guide](ci-cd-macos.md) | [Complete Workflow Example](../../.github/workflows/test-install.yml)

## Why Test on Linux?

- **Package manager variations**: Different Linux distributions (Ubuntu, Debian, RHEL, etc.) have different behavior
- **Bash compatibility**: Ensure bash scripts work on various shell environments
- **Path handling**: Linux uses Unix-style paths which differ from macOS
- **APT prerequisites**: Installation of git, curl, xz-utils, unzip varies by distribution

## GitHub Actions Setup

### Ubuntu/Debian Installer Testing

Add this job to your `.github/workflows/ci.yml`:

```yaml
linux-install:
  runs-on: ubuntu-latest
  name: "Test install.sh (Linux/Ubuntu)"
  
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

### Multiple Linux Distributions

To test on different distributions, use a matrix:

```yaml
linux-multi-distro:
  strategy:
    matrix:
      container:
        - ubuntu:22.04
        - ubuntu:24.04
        - debian:bookworm
  
  runs-on: ubuntu-latest
  container: ${{ matrix.container }}
  name: "Test install.sh (${{ matrix.container }})"
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Install curl (required for installer)
      run: |
        apt-get update
        apt-get install -y curl
    
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

### Testing Just Commands on Linux

```yaml
linux-justfile-testing:
  runs-on: ubuntu-latest
  name: "Test just recipes (Linux)"
  
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

### Testing with Custom Shell

```yaml
linux-custom-shell:
  strategy:
    matrix:
      shell:
        - bash
        - sh
  
  runs-on: ubuntu-latest
  name: "Test install.sh with ${{ matrix.shell }}"
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Run installer
      shell: ${{ matrix.shell }}
      run: |
        bash <(curl -fsSL ${{ github.server_url }}/${{ github.repository }}/raw/${{ github.ref_name }}/install.sh)
    
    - name: Verify installation
      shell: ${{ matrix.shell }}
      run: |
        ragtime --version
        proto --version
        moon --version
        uv --version
        just --version
```

### Testing Prerequisites Installation

```yaml
linux-minimal-system:
  runs-on: ubuntu-latest
  name: "Test install.sh with minimal prerequisites"
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Remove optional tools (test minimal system)
      run: |
        # Simulate a minimal system without some tools
        sudo rm -f /usr/bin/xz || true
        sudo rm -f /usr/bin/unzip || true
    
    - name: Run bash installer
      shell: bash
      run: |
        bash <(curl -fsSL ${{ github.server_url }}/${{ github.repository }}/raw/${{ github.ref_name }}/install.sh)
    
    - name: Verify installation
      shell: bash
      run: |
        ragtime --version
        proto --version
```

### Testing Behind Simulated Proxy

```yaml
linux-proxy-simulation:
  runs-on: ubuntu-latest
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
        if [ -f ~/.proto/.prototools ]; then
          echo "✓ .prototools created successfully"
          cat ~/.proto/.prototools
        else
          echo "✗ .prototools not found"
          exit 1
        fi
```

## Common Issues on Linux

### curl Not Found

Some minimal containers don't have curl pre-installed:

```bash
# In your CI step, install curl first
apt-get update && apt-get install -y curl
```

### Missing Prerequisites

The installer tries to auto-install on Debian/Ubuntu. If it fails:

```bash
# Manual prerequisite installation
sudo apt-get update
sudo apt-get install -y git curl xz-utils unzip
```

### Shell Not Found

On some systems, `/bin/bash` might not exist. Use `/bin/sh`:

```bash
sh <(curl -fsSL https://...)
```

### HOME Not Set

In containerized CI, `$HOME` might not be set. Set it explicitly:

```bash
export HOME=/root  # or /home/runner
bash <(curl -fsSL ...)
```

## Best Practices

✅ **Test multiple distributions** — Use matrix to test Ubuntu, Debian, etc.  
✅ **Test minimal systems** — Remove optional tools to test edge cases  
✅ **Test proxy scenarios** — Set env vars to simulate corporate networks  
✅ **Test different shells** — Try bash, sh, and other shells  
✅ **Test just commands** — Ensure recipes work after installation  
✅ **Check .prototools creation** — Verify proxy config is generated  

## References

- [GitHub Actions: Linux Runners](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners)
- [GitHub Actions: Containers](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idcontainer)
- [Proto: Installation](https://moonrepo.dev/docs/proto/install)
- [Bash Scripting Guide](https://www.gnu.org/software/bash/manual/)
