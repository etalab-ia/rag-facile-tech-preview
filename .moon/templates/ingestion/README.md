# ingestion

Document ingestion package for Ragtime. Parses and extracts text from files (PDF, Markdown, HTML) using pluggable providers.

## Providers

- **local** — Local PDF parsing using pypdf (no external API required)
- **albert** — Server-side parsing via Albert API with OCR and multi-format support

## Usage

```python
from ragtime.ingestion import get_provider

provider = get_provider()  # reads ragtime.toml
text = provider.extract_text("document.pdf")
context = provider.process_file("document.pdf")
```

The provider is configured in `ragtime.toml`:

```toml
[ingestion]
provider = "local"  # or "albert"
```
