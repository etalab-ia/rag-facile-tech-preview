# Changelog

## [0.2.0](https://github.com/etalab-ia/ragtime/compare/cli-v0.1.0...cli-v0.2.0) (2026-02-03)


### Features

* add bootstrap installer and auto-download templates ([66a2015](https://github.com/etalab-ia/ragtime/commit/66a2015ab374cd607d1b098db800d7479d91dcd3))
* add bootstrap installer and bundle templates in CLI ([c876a4e](https://github.com/etalab-ia/ragtime/commit/c876a4e935d5072d4485dae4a50547cf8a81bc11))
* add chainlit-chat template and generator ([abfb788](https://github.com/etalab-ia/ragtime/commit/abfb788876b3086b87b76926b76d91a83a1a10e5))
* add just commands for template generation and instantiation ([1f2619d](https://github.com/etalab-ia/ragtime/commit/1f2619db30dc1a29f665b5b5950e5544f9966d53))
* add moon tasks, Justfile, and CONTRIBUTING.md ([0d07041](https://github.com/etalab-ia/ragtime/commit/0d07041a0d73c86281cb0007eb86b91e9ea4d4f2))
* add reflex-chat app and downgrade to Python 3.13 ([7395391](https://github.com/etalab-ia/ragtime/commit/7395391aeab4acc28494cd3c4a79b0f2c19c1b00))
* add reflex-chat application and Albert API integration ([aa8be55](https://github.com/etalab-ia/ragtime/commit/aa8be55eca1b8ccd58d91cd5eec7269e479ab9ba))
* auto-install proto and moon if not present ([4aea431](https://github.com/etalab-ia/ragtime/commit/4aea4316944822b3f63de46992d4684313b1edb9))
* auto-run uv sync and start dev server after generation ([92d0090](https://github.com/etalab-ia/ragtime/commit/92d00901e2d66ee1e903861ce3c6552afd8fc531))
* bundle templates in CLI package distribution ([6408718](https://github.com/etalab-ia/ragtime/commit/6408718d8902f0c13684e5d88ff229898758e19d))
* complete rf generate workspace command ([06a7cae](https://github.com/etalab-ia/ragtime/commit/06a7cae9bbea65f4bedbf475ba8b9049b087721c))
* extract pdf-context package and fix templates ([9cac265](https://github.com/etalab-ia/ragtime/commit/9cac2657e3d441ab7f5c6dc9e98b545f90fce527))
* extract pdf-context package and fix templates ([fd021ee](https://github.com/etalab-ia/ragtime/commit/fd021eeef2d283996e58c730a8af705ead5d8886))
* implement hybrid LibCST + ast-grep pipeline for chainlit-chat ([6634c86](https://github.com/etalab-ia/ragtime/commit/6634c86c9f59813ee14f9d922d47bc0db29842e3))
* implement hybrid LibCST + ast-grep pipeline for template generation ([ba385ba](https://github.com/etalab-ia/ragtime/commit/ba385ba275932dc158f504b684ed47931b5eb8cf))
* implement Init + Patch architecture for workspace generation ([7d8ff6a](https://github.com/etalab-ia/ragtime/commit/7d8ff6a5cfe4e9c144dc5404d78b1300792f4d5f))
* Implement PDF upload and context integration for the Reflex chat application. ([492b051](https://github.com/etalab-ia/ragtime/commit/492b0515ca08caa43aaf85bd1d525fbbe03f1942))
* Initial RAG starter kit setup ([80ce74e](https://github.com/etalab-ia/ragtime/commit/80ce74ea33d62580b2fd6edb46d56ba65b62db66))
* Initial setup of RAG starter kit (v0.1.0) ([6135ebb](https://github.com/etalab-ia/ragtime/commit/6135ebb283fa0c3baf3fe23bf4fbc1a72a45b42c))
* make CLI installable via uv tool install ([27db58a](https://github.com/etalab-ia/ragtime/commit/27db58a871f0cff1da0c8b8a19840c4eea5333bd))
* make CLI installable via uv tool install ([63ec4ab](https://github.com/etalab-ia/ragtime/commit/63ec4ab2cb4a993c6b9914db098ce03e0eb0867c))
* parameterize env vars and fix grit usage ([72be38a](https://github.com/etalab-ia/ragtime/commit/72be38a8723e2295f1697fe4842be0469488cfa0))
* prompt for env config and create .env file during generation ([6219006](https://github.com/etalab-ia/ragtime/commit/62190067ad9df600b3997b1e3f9bcc83e4bce688))
* refactor template generation cli for multi-app support ([88990d2](https://github.com/etalab-ia/ragtime/commit/88990d2c0bfccfbe2aa57b4438f01dce29d58d2f))
* **reflex-chat:** Add PDF Context Support and Refined UI ([13c51f5](https://github.com/etalab-ia/ragtime/commit/13c51f5678083aada30bd242651202ed4d7bcd90))
* rename CLI to ragtime and add ASCII banner ([01a0165](https://github.com/etalab-ia/ragtime/commit/01a01656fc140f8a4be1b21dcf8166eddb2730d9))
* rename CLI to ragtime and add ASCII banner ([fdf917b](https://github.com/etalab-ia/ragtime/commit/fdf917b5d51c5ab42b8365015bcc29031c624008))
* rf generate workspace - one command to running RAG app ([d520536](https://github.com/etalab-ia/ragtime/commit/d520536882b34ab853cf2d43da028b05b71df192))
* support reflex-chat in template generation CLI ([06040e1](https://github.com/etalab-ia/ragtime/commit/06040e1cb891c786ae32c6de695653320d5b8ff5))
* **templates:** support env var API keys and fix uv sync warning ([a26a598](https://github.com/etalab-ia/ragtime/commit/a26a59862c7bedd95840673ecb800fdc9e771b95))
* update default OpenAI API key help message, base URL, and model to Albert API endpoints. ([519e96f](https://github.com/etalab-ia/ragtime/commit/519e96f4033cfc656e314d04fb392c210bb83521))


### Bug Fixes

* add proto paths to PATH after installation ([6a289ff](https://github.com/etalab-ia/ragtime/commit/6a289ff1db79522aa3e607c2f6dc265fac848f3f))
* Address PR review feedback (Python 3.14.2, ruff 0.9.3, ragtime) ([b6c8ea0](https://github.com/etalab-ia/ragtime/commit/b6c8ea02afacbed63e1d68971a22f59b0418c517))
* **cli:** rename main app file and parameterize imports in reflex template ([c95823d](https://github.com/etalab-ia/ragtime/commit/c95823d9400b5de0a25b6a42efdeef2e9061cb39))
* exclude template directories from ruff checks ([730ea37](https://github.com/etalab-ia/ragtime/commit/730ea37a4b9303ba47dfe1dca0f84539543bf0a2))
* fix test mocks for workspace generation flow ([bab1fbb](https://github.com/etalab-ia/ragtime/commit/bab1fbb2a6167dfdb9a40be476ad4fc6ceedf5f2))
* rename README.md to .jinja for full parameterization ([d4e4a66](https://github.com/etalab-ia/ragtime/commit/d4e4a66ca51861f5b527c2eebc1f652d8faa902a))
* resolve ast-grep warnings and improve reflex parameterization ([59acb4b](https://github.com/etalab-ia/ragtime/commit/59acb4b17620595427d1ea8aaf068162607e50a1))
* resolve linting and formatting issues ([ecf8e84](https://github.com/etalab-ia/ragtime/commit/ecf8e844fda2449a89cabdc8056f7f1bdb4721ac))
* use --yes flag for proto install to avoid interactive prompt issues ([07f9d63](https://github.com/etalab-ia/ragtime/commit/07f9d632780b5fc3e8835404aa2739f49a801234))
* use .jinja extension for parameterized template files ([d44f573](https://github.com/etalab-ia/ragtime/commit/d44f573f78c3ea1cbc30d20767ebb1eae5ffcdcd))


### Documentation

* improve template READMEs for standalone use and add CLI README ([c511de2](https://github.com/etalab-ia/ragtime/commit/c511de2f142054ff2f94c5b347082bf899e6b6f2))
