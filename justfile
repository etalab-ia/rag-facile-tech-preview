default:
	@just --list

# Lint all code
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .

# Type check all code
type-check:
	uv run ty

# Run the Reflex Chat application
reflex-chat:
	cd apps/reflex-chat && uv run reflex run

# Run the ChainLit Chat application
chainlit-chat:
        cd apps/chainlit-chat && uv run chainlit run app.py -w

# Run the Streamlit Admin application
admin:
        cd apps/admin && uv run streamlit run src/admin/main.py

# Install all dependencies and setup the workspace
setup:
        uv sync
        uv run pre-commit install
        @echo "✓ Pre-commit hooks installed"

# Generate all app templates
gen-templates:
        uv run --project apps/cli rf template generate --app chainlit-chat
        uv run --project apps/cli rf template generate --app reflex-chat

# Create a new application from a template using Moon
# Usage: just create-app [app-type] [destination]
create-app app_type="chainlit-chat" destination="":
        #!/usr/bin/env bash
        set -euo pipefail
        TYPE="{{app_type}}"
        # Normalize input
        if [[ "$TYPE" == "chainlit" ]] || [[ "$TYPE" == "chainlit-app" ]]; then TYPE="chainlit-chat"; fi
        if [[ "$TYPE" == "reflex" ]] || [[ "$TYPE" == "reflex-app" ]]; then TYPE="reflex-chat"; fi

        if [ "$TYPE" != "chainlit-chat" ] && [ "$TYPE" != "reflex-chat" ]; then
            echo "Error: Invalid app type '{{app_type}}'. Valid options are: chainlit-chat, reflex-chat (or shorthands like 'chainlit', 'reflex')"
            exit 1
        fi

        if [ ! -d ".moon/templates/$TYPE" ]; then just gen-templates; fi

        # Check for API Key in environment
        VAR_ARGS=""
        if [ -n "${ALBERT_API_KEY:-}" ]; then
            VAR_ARGS="--openai_api_key $ALBERT_API_KEY"
            echo "Using ALBERT_API_KEY from environment"
        elif [ -n "${OPENAI_API_KEY:-}" ]; then
            VAR_ARGS="--openai_api_key $OPENAI_API_KEY"
            echo "Using OPENAI_API_KEY from environment"
        fi

        # Pass project_name automatically based on destination
        FINAL_DEST="{{if destination == "" { "$TYPE" } else { destination}}}"
        NAME=$(basename "$FINAL_DEST")

        # If FINAL_DEST is absolute, generate in a temp local dir and move/copy
        if [[ "$FINAL_DEST" == /* ]]; then
            TEMP_GEN_DIR=".moon/gen-temp"
            rm -rf "$TEMP_GEN_DIR"
            # We generate inside the temp dir. Moon will create it if we provide it as DEST.
            moon generate "$TYPE" "$TEMP_GEN_DIR" --force -- --project_name "$NAME" $VAR_ARGS

            # Post-process: rename .env.template to .env
            if [ -f "$TEMP_GEN_DIR/.env.template" ]; then
                mv "$TEMP_GEN_DIR/.env.template" "$TEMP_GEN_DIR/.env"
            fi

            # Move to final destination
            echo "Moving generated app to $FINAL_DEST..."
            mkdir -p "$(dirname "$FINAL_DEST")"
            # Use cp -a to preserve permissions and handles existing dirs better than mv in some cases
            cp -a "$TEMP_GEN_DIR/." "$FINAL_DEST/"
            rm -rf "$TEMP_GEN_DIR"
            echo "✔ Generated app created at $FINAL_DEST"
        else
            moon generate "$TYPE" "$FINAL_DEST" -- --project_name "$NAME" $VAR_ARGS
            if [ -f "$FINAL_DEST/.env.template" ]; then
                mv "$FINAL_DEST/.env.template" "$FINAL_DEST/.env"
            fi
        fi
