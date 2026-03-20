# Ragtime CLI

The `ragtime` CLI helps you generate RAG workspaces for the French government.

## Installation

### Option 1: Install Script (Recommended)

One command installs the entire toolchain (proto, moon, uv) and the CLI:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/etalab-ia/ragtime/main/install.sh)
```

Then **restart your terminal** (or run the `source` command shown by the installer).

### Option 2: Manual Installation

If you already have `uv` installed:

```bash
uv tool install ragtime --from git+https://github.com/etalab-ia/ragtime.git#subdirectory=apps/cli
```

To upgrade:

```bash
uv tool install ragtime --force --from git+https://github.com/etalab-ia/ragtime.git#subdirectory=apps/cli
```

### Option 3: One-time Usage

Run directly without installing:

```bash
uvx --from git+https://github.com/etalab-ia/ragtime.git#subdirectory=apps/cli ragtime [command]
```

## Usage

```bash
# Show all available commands
ragtime --help

# Check version
ragtime --version

# Setup a new workspace
ragtime setup my-rag-app
```

## Commands

### `setup`

Setup a new RAG workspace with your choice of structure, frontend, and configuration preset.

```bash
ragtime setup <name>
```

The CLI will guide you through:
1. **Project structure** - Choose between:
   - **Simple** - Flat structure, single app, easy to understand (recommended for getting started)
   - **Monorepo** - Multi-app workspace with shared packages (for larger projects)
2. **Configuration preset** - Choose from Balanced, Fast, Accurate, Legal, or HR. This automatically sets up your model, temperature, and RAG parameters.
3. **Frontend selection** - Choose Chainlit or Reflex
4. **Environment configuration** - Set your Albert API key (the preset handles base URLs and model IDs)

See the main [README](../../README.md) for detailed comparison of project structures and presets.

### `generate-dataset`

Generate synthetic Q/A evaluation datasets from your documents. Supports multiple providers: Letta Cloud or self-hosted Albert API.

```bash
ragtime generate-dataset ./docs -o golden_dataset.jsonl -n 50 --provider letta
```

**Options:**
- `-p, --provider` - Provider to use (`letta` or `albert`) - **required**
- `-o, --output` - Output JSONL file path (default: `golden_dataset.jsonl`)
- `-n, --samples` - Target number of Q/A pairs (default: 50)
- `--agent-id` - Data Foundry agent ID for Letta (or set `DATA_FOUNDRY_AGENT_ID` env var)
- `--debug` - Enable debug logging (verbose output to console + file)

**For Letta Cloud Provider:**

```bash
export LETTA_API_KEY="your-api-key"           # Get at https://app.letta.com/api-keys
export DATA_FOUNDRY_AGENT_ID="agent-xxx"      # Pre-configured agent ID

ragtime generate-dataset ./docs -o golden_dataset.jsonl --provider letta
```

**For Albert API Provider (Self-Hosted):**

```bash
export OPENAI_API_KEY="your-api-key"          # Albert API key
export OPENAI_BASE_URL="http://localhost:8000"  # Albert API endpoint
export OPENAI_MODEL="mistral-7b"              # Model to use

ragtime generate-dataset ./docs -o golden_dataset.jsonl --provider albert
```

**Output:**

Creates two files:

1. **JSONL dataset** (`golden_dataset.jsonl`) - Ragas-compatible format with French Q/A pairs:
   ```json
   {
     "user_input": "Quel est le délai de recours administratif?",
     "retrieved_contexts": ["Le délai de recours est de deux mois..."],
     "reference": "Le délai de recours administratif est de deux mois.",
     "_metadata": {"source_file": "code.pdf", "quality_score": 0.95}
   }
   ```

2. **Debug log** (`golden_dataset.jsonl.log`) - Trace of all interactions:
   - INFO level: Document uploads, provider IDs, session progress
   - DEBUG level (with `--debug` flag): Full prompts and responses

**Debug Mode:**

```bash
# Standard mode - clean output, INFO logs only to file
ragtime generate-dataset ./docs -o output.jsonl --provider albert

# Debug mode - verbose console + file logging
ragtime generate-dataset ./docs -o output.jsonl --provider albert --debug
```

**Debug Features:**
- See exact prompts sent to LLM
- View complete LLM responses
- Track provider IDs (Letta Folder ID, Albert Collection ID, Conversation ID)
- Monitor document uploads
- Full error traces for troubleshooting

### `config`

Manage RAG configuration with presets, validation, and runtime customization.

```bash
# Show all config commands
ragtime config --help
```

#### `config show`

Display current configuration in multiple formats:

```bash
# Show as formatted table (default)
ragtime config show

# Show as TOML
ragtime config show --format toml

# Show as JSON
ragtime config show --format json

# Show only a specific section
ragtime config show --section generation

# Show environment variable documentation
ragtime config show --env-docs
```

**Options:**
- `-c, --config` - Path to config file (default: `ragtime.toml`)
- `-f, --format` - Output format: `table`, `toml`, or `json`
- `-s, --section` - Show only specific section (e.g., `generation`, `retrieval`)
- `--env-docs` - Show environment variable override documentation

#### `config validate`

Validate configuration file and show warnings for common issues:

```bash
# Validate default config
ragtime config validate

# Validate specific file
ragtime config validate --config custom.toml
```

**Checks for:**
- Schema compliance (required fields, valid types)
- Common misconfigurations (e.g., `top_k` < `top_n`)
- Dangerous settings (e.g., infinite regeneration loops)

#### `config set`

Update configuration values via dot notation:

```bash
# Set generation model
ragtime config set generation.model openweight-large

# Set temperature
ragtime config set generation.temperature 0.5

# Enable hallucination detection
ragtime config set hallucination.enabled true

# Set retrieval top_k
ragtime config set retrieval.top_k 20
```

**Options:**
- `-c, --config` - Path to config file (default: `ragtime.toml`)
- `--create` - Create config file if it doesn't exist

**Supported types:**
- Boolean: `true`, `false`, `yes`, `no`, `1`, `0`
- Integer: `10`, `100`
- Float: `0.5`, `0.95`
- String: Any other value

#### `config preset`

Manage configuration presets:

```bash
# List available presets
ragtime config preset list

# Show detailed preset configuration
ragtime config preset show legal

# Apply a preset
ragtime config preset apply balanced

# Apply to custom location
ragtime config preset apply legal --output config/legal.toml

# Compare two presets
ragtime config preset compare fast accurate
```

**Available Presets:**
- `balanced` - Recommended default (quality/speed tradeoff)
- `fast` - Speed-optimized (smaller models, skip reranking)
- `accurate` - Quality-optimized (larger models, hallucination detection)
- `legal` - Legal documents (strict citations, low temperature, accuracy validation)
- `hr` - HR policies (privacy-aware, semantic search, clear attribution)

**Options:**
- `-o, --output` - Output file path (default: `ragtime.toml`)
- `-f, --force` - Overwrite without confirmation

#### Environment Variable Overrides

All configuration values can be overridden via environment variables:

```bash
# Override any setting using RAG_<SECTION>_<KEY> format
export RAG_GENERATION_MODEL=openweight-large
export RAG_GENERATION_TEMPERATURE=0.5
export RAG_RERANKING_ENABLED=true
export RAG_RETRIEVAL_TOP_K=20

# Run with overrides
ragtime config show  # Shows overridden values
```

**How it works:**
1. Load base configuration from `ragtime.toml` (or defaults)
2. Apply environment variable overrides
3. Validate final configuration

See the [Configuration Guide](../../packages/rag-config/README.md) for complete documentation.

## Development

The CLI is built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/).

For development setup and contribution guidelines, see the main [CONTRIBUTING.md](../../CONTRIBUTING.md) file.

**Source code structure:**
- `src/cli/` - Main CLI package
- `src/cli/commands/` - Command definitions
