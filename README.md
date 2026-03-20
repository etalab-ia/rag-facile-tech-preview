# Ragtime — A modular RAG pipeline (alpha)

[![Release](https://img.shields.io/github/v/release/etalab-ia/ragtime-tech-preview?sort=date&style=flat-square)](https://github.com/etalab-ia/ragtime-tech-preview/releases)
[![License](https://img.shields.io/github/license/etalab-ia/ragtime-tech-preview?style=flat-square)](LICENSE)

```
 ██████╗  █████╗  ██████╗████████╗██╗███╗   ███╗███████╗
 ██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██║████╗ ████║██╔════╝
 ██████╔╝███████║██║  ███╗  ██║   ██║██╔████╔██║█████╗
 ██╔══██╗██╔══██║██║   ██║  ██║   ██║██║╚██╔╝██║██╔══╝
 ██║  ██║██║  ██║╚██████╔╝  ██║   ██║██║ ╚═╝ ██║███████╗
 ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   ╚═╝   ╚═╝╚═╝     ╚═╝╚══════╝
```

A modular RAG pipeline for the French government, powered by the [Albert API](https://albert.sites.beta.gouv.fr/).

## Prerequisites

- An **Albert API key** — [request one here](https://albert.sites.beta.gouv.fr/)
- **curl** (pre-installed on macOS / Linux / WSL / Git Bash)

## Install

Linux / macOS / WSL / Windows (Git Bash):

```bash
curl -fsSL https://raw.githubusercontent.com/etalab-ia/ragtime-tech-preview/main/install.sh | bash
```

## Quick Start

```bash
# Create your RAG project (prompts for API key and preferences)
ragtime setup mon-projet

# Start your app
cd mon-projet && just run
```

Your app opens at **http://localhost:8000** — upload documents and ask questions.

```bash
# Chat with the interactive RAG learning assistant
just learn
```

## Upgrade

Re-run the installer to get the latest version:

```bash
curl -fsSL https://raw.githubusercontent.com/etalab-ia/ragtime-tech-preview/main/install.sh | bash
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/guides/getting-started.md) | Detailed installation, available commands, advanced setup |
| [Understanding the RAG Pipeline](docs/guides/rag-pipeline.md) | What each stage of the pipeline does and why it matters |
| [`ragtime.toml` Reference](docs/reference/ragfacile-toml.md) | Every configuration option, presets comparison, environment overrides |
| [Evaluation Guide](docs/guides/evaluation.md) | Generate synthetic datasets and measure RAG quality |
| [Components Reference](docs/reference/components.md) | Albert Client SDK, frontend apps, and modules |
| [Windows Setup](docs/guides/windows-setup.md) | Installation on Windows via Git Bash |
| [Proxy & Network Setup](docs/guides/proxy-setup.md) | Install behind corporate proxies and VPNs |

## Contributing

Want to contribute to Ragtime itself? See [CONTRIBUTING.md](CONTRIBUTING.md) for the architecture overview and development setup.

## License

See [LICENSE](LICENSE) for details.
