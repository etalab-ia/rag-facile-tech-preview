# RAG Facile Installation on Corporate/Restricted Networks

**Issue #46**: Proto plugin installation fails on networks with proxies, VPNs, or restrictive firewalls.

This guide explains how to install RAG Facile when behind a corporate proxy or VPN, and provides troubleshooting steps.

## Quick Start

If you're behind a proxy, set the environment variables before running the installer:

```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

bash <(curl -fsSL https://raw.githubusercontent.com/etalab-ia/rag-facile/main/install.sh)
```

The installer will automatically:
1. **Detect** your proxy settings
2. **Configure** proto to use your proxy
3. **Provide guidance** if SSL certificate issues occur

## How It Works

### What Happens During Installation

1. **Proto binary installation** (direct download via curl)
   - This usually works even behind proxies
   
2. **Plugin installation** (where failures occur)
   - Proto installs "moon" plugin from GitHub/GHCR
   - Plugin is cached in `~/.proto/plugins/`
   - Requires network access to reach GitHub

3. **Package managers** (uv, just)
   - Downloaded and installed via proto
   
4. **RAG Facile CLI** (final step)
   - Installed via uv tool

### Where Proxy Issues Occur

**Most common failure point**: Step 2 - `proto install moon`

This fails because:
- Moon WASM plugin must be downloaded from GitHub
- Corporate proxies may block GitHub or require special configuration
- SSL/TLS inspection by proxy creates certificate validation errors

## Troubleshooting

### Symptom: Connection Timeout

```
Error: Failed to download plugin
caused by: connection timed out
```

**Causes**:
- Proxy server not configured
- Proxy blocks GitHub/GHCR URLs
- Firewall rules block outbound connections

**Solutions**:

1. **Verify proxy environment variables are set**:
   ```bash
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   ```

2. **Test connectivity through proxy**:
   ```bash
   curl -x $HTTPS_PROXY -I https://github.com
   curl -x $HTTPS_PROXY -I https://ghcr.io
   ```

3. **Manually configure proto** if the installer's auto-detection didn't work:
   ```bash
   mkdir -p ~/.proto
   cat > ~/.proto/.prototools << 'EOF'
   [settings.http]
   proxies = ["https://proxy.company.com:8080"]
   
   [settings.offline]
   timeout = 5000
   EOF
   ```

4. **If behind corporate firewall**, your network team may need to whitelist:
   - `github.com`
   - `ghcr.io` (GitHub Container Registry)
   - `raw.githubusercontent.com`

### Symptom: SSL Certificate Error

```
Error: certificate verify failed
caused by: Self signed certificate
```

**Causes**:
- Corporate proxy performs SSL inspection (MITM)
- Proxy creates self-signed certificates for HTTPS traffic
- Proto can't verify the certificate

**Solutions**:

1. **Export your corporate root certificate**:
   
   Steps depend on your system:
   
   **macOS**:
   ```bash
   # Open Keychain Access
   # Find your corporate proxy/CA certificate
   # Right-click → Export "Company CA"
   # Save as corporate-ca.pem
   ```
   
   **Linux (Ubuntu/Debian)**:
   ```bash
   # Check if certificate is already installed
   ls /etc/ssl/certs/
   
   # Or use your company's certificate management
   # Copy certificate to a .pem file
   ```
   
   **Windows (WSL)**:
   ```bash
   # Export from Windows certificate store
   # Or get from your IT team
   ```

2. **Configure proto to use your certificate**:
   ```bash
   cat >> ~/.proto/.prototools << 'EOF'
   
   [settings.http]
   root-cert = "/path/to/corporate-ca.pem"
   EOF
   ```

3. **Test the configuration**:
   ```bash
   proto install moon --log trace
   ```

4. **Last resort**: Allow invalid certificates (NOT RECOMMENDED)
   ```bash
   cat >> ~/.proto/.prototools << 'EOF'
   
   [settings.http]
   allow-invalid-certs = true
   EOF
   ```

### Symptom: Offline Mode Detection Fails

```
proto: offline mode detected
Error: Cannot install tools while offline
```

**Causes**:
- Proto checks internet connectivity by pinging hosts
- Proxy blocks DNS or pinging endpoints
- Proto thinks you're offline when you're actually connected

**Solutions**:

1. **Override default connectivity checks**:
   ```bash
   cat >> ~/.proto/.prototools << 'EOF'
   
   [settings.offline]
   override-default-hosts = true
   custom-hosts = ["8.8.8.8:53"]
   timeout = 5000
   EOF
   ```

2. **Or bypass version checks entirely** (if tool is already installed):
   ```bash
   export PROTO_BYPASS_VERSION_CHECK=1
   proto install moon
   ```

## Advanced: URL Rewriting for Internal Mirrors

If your company has an internal mirror of GitHub packages, you can configure URL rewrites:

```bash
cat > ~/.proto/.prototools << 'EOF'
[settings.http]
proxies = ["https://proxy.company.com:8080"]

[settings.url-rewrites]
# Redirect GitHub to internal mirror
"github.com/(\\w+)/(\\w+)" = "github-mirror.company.com/$1/$2"

# Redirect GHCR to internal registry
"ghcr.io/(.*)" = "registry.company.com/$1"
EOF
```

## Simulating the Issue (For Testing)

If you want to test proxy support, you can simulate the issue locally:

### Using mitmproxy

```bash
# Install mitmproxy
brew install mitmproxy  # macOS
apt install mitmproxy   # Linux
pip install mitmproxy   # Python

# Start proxy server
mitmproxy --mode regular -p 8080

# In another terminal, run installer with proxy
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
bash <(curl -fsSL https://raw.githubusercontent.com/etalab-ia/rag-facile/main/install.sh)
```

### Blocking Network Access

```bash
# macOS: Block GitHub with firewall
sudo pfctl -f /etc/pf.conf
sudo bash -c 'echo "block out proto tcp from any to any port 443" >> /etc/pf.conf'
sudo pfctl -e

# Linux: Block GitHub with iptables
sudo iptables -A OUTPUT -d github.com -j DROP
sudo iptables -A OUTPUT -d ghcr.io -j DROP
```

## Configuration Files Reference

### Proto Configuration (`~/.proto/.prototools`)

```toml
# ============================================
# HTTP/Proxy Settings
# ============================================

[settings.http]
# Single or multiple proxies (tried in order)
proxies = ["https://proxy.company.com:8080"]

# Mark HTTP proxies as secure (normally insecure)
secure-proxies = ["http://internal-proxy:8080"]

# Root certificate for SSL verification
root-cert = "/path/to/corporate-ca.pem"

# Emergency: Allow invalid certificates
allow-invalid-certs = true

# ============================================
# Offline Mode (for connectivity checks)
# ============================================

[settings.offline]
# Custom hosts to ping for internet check
custom-hosts = ["8.8.8.8:53", "proxy.company.com:80"]

# Override default Google/Cloudflare DNS checks
override-default-hosts = true

# Timeout for connectivity checks (milliseconds)
timeout = 5000

# ============================================
# URL Rewriting (for internal mirrors)
# ============================================

[settings.url-rewrites]
"github.com/(\\w+)/(\\w+)" = "github-mirror.company.com/$1/$2"
"ghcr.io/(.*)" = "registry.company.com/$1"
```

## Environment Variables vs Configuration Files

### Environment Variables (Quick)
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1
```

**Pros**: Quick, per-session
**Cons**: Must set every time, installer auto-detection only works once

### Configuration File (Persistent)
```bash
# ~/.proto/.prototools
[settings.http]
proxies = ["https://proxy.company.com:8080"]
```

**Pros**: Persists across sessions, more configuration options
**Cons**: Requires manual file creation

## Getting Help

If you're still having issues:

1. **Check proto logs**:
   ```bash
   # Proto creates logs in ~/.proto
   cat ~/.proto/logs/*.log
   ```

2. **Run with debug output**:
   ```bash
   proto install moon --log trace
   ```

3. **Report an issue**:
   - [RAG Facile GitHub Issues](https://github.com/etalab-ia/rag-facile/issues)
   - [Proto GitHub Issues](https://github.com/moonrepo/proto/issues)

4. **Ask your IT team**:
   - What proxy server URL should I use?
   - What domains do I need to whitelist?
   - Can they provide the root CA certificate?

## For IT Teams / System Administrators

If you're setting up RAG Facile for your organization:

### Required Network Access

The installer needs outbound access to:
- `github.com` - Source repository
- `ghcr.io` - GitHub Container Registry (proto plugins)
- `moonrepo.dev` - Proto installer script
- `just.systems` - Just task runner installer

### Proxy Configuration

If using a corporate proxy:
1. Ensure it's configured in system environment variables
2. If using SSL inspection, export and distribute the root CA certificate
3. Whitelist the above domains if using allowlist rules

### SSL/TLS Inspection

If your proxy performs SSL inspection:
1. Export the root certificate from your proxy appliance
2. Distribute to users as `.pem` file
3. Document the path in your setup instructions
4. Users add to `~/.proto/.prototools`:
   ```toml
   [settings.http]
   root-cert = "/path/to/company-ca.pem"
   ```

## Related Documentation

- [Proto Configuration](https://moonrepo.dev/docs/proto/config)
- [Proto FAQ - Troubleshooting](https://moonrepo.dev/docs/proto/faq)
- [Proto GitHub Repository](https://github.com/moonrepo/proto)
- [RAG Facile Installation](https://github.com/etalab-ia/rag-facile#installation)
