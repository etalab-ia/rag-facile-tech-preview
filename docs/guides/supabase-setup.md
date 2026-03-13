# Supabase Setup Guide

rag-facile uses [Supabase](https://supabase.com) (self-hosted) for persistent storage when you need:

- **Conversation history** — resume past chats in Chainlit
- **RAG tracing** — query logs, retrieved chunks, feedback, and latency data
- **User authentication** — password-based login for Chainlit
- **Supabase Studio** — visual dashboard to browse your data

> **SQLite remains the default.** Supabase is optional — enable it only when you need persistence across deployments or multi-user support.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Supabase CLI](https://supabase.com/docs/guides/cli/getting-started) (`brew install supabase/tap/supabase` on macOS)

## Quick Start

### 1. Start the local Supabase stack

From the project root:

```bash
supabase start
```

This starts PostgreSQL, Studio, Auth, Storage, and PostgREST. The first run downloads Docker images (~2 min).

### 2. Apply database migrations

```bash
supabase db push
```

This applies the SQL migrations in `supabase/migrations/`:

| Migration | Purpose |
|-----------|---------|
| `00000000000000_tracing.sql` | RAG tracing tables (traces, config snapshots, RAGAS export view) |
| `00000000000001_chainlit.sql` | Chainlit data layer (users, threads, steps, elements, feedbacks) |

### 3. Get the connection string

```bash
supabase status
```

Copy the `DB URL` value (looks like `postgresql://postgres:postgres@127.0.0.1:54322/postgres`).

### 4. Configure rag-facile

Add to your `.env`:

```bash
# Supabase Postgres connection
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

Update `ragfacile.toml`:

```toml
[tracing]
provider = "postgres"
```

The provider automatically reads `DATABASE_URL` from the environment. You can also set `connection_string` explicitly in the TOML if preferred:

```toml
[tracing]
provider = "postgres"
connection_string = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
```

### 5. Verify

Open Supabase Studio at http://localhost:54323 to browse tables.

## Enable Chainlit Authentication

When `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set, Chainlit shows a login form and validates credentials against Supabase Auth (GoTrue).

### 1. Generate a JWT secret

Chainlit requires a secret to sign session tokens:

```bash
chainlit create-secret
```

Copy the output value.

### 2. Get Supabase credentials

```bash
supabase status
```

Copy the `API URL` and `anon key` values.

### 3. Add to `.env`

```bash
# Required: JWT secret for Chainlit session tokens
CHAINLIT_AUTH_SECRET=your_chainlit_auth_secret_here

# Supabase Auth (enables Chainlit login)
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=your_anon_key_here
```

### 4. Create users

In Supabase Studio (http://localhost:54323):

1. Go to **Authentication** → **Users**
2. Click **Create new user**
3. Enter email and password
4. Toggle **Auto Confirm User** (for local development)

### 5. Restart Chainlit

```bash
just run chainlit
```

The login form appears. Sign in with the user you created.

> **Note**: Auth is optional. Without `SUPABASE_URL` and `SUPABASE_ANON_KEY`, Chainlit runs without login (current behavior). `CHAINLIT_AUTH_SECRET` is only required when auth is enabled.

## Colima Users (macOS)

If you use [Colima](https://github.com/abiosoft/colima) instead of Docker Desktop, you may hit permission errors on `supabase start`:

**`chown ... permission denied`** — Colima's default mount type blocks ownership changes.

Switch to macOS Virtualization.framework:

```bash
colima stop
colima delete
colima start --vm-type=vz
```

**`mkdir .../docker.sock: operation not supported`** — `virtiofs` can't handle bind-mounting Unix sockets.

Export `DOCKER_HOST` so the Supabase CLI uses the standard socket path:

```bash
export DOCKER_HOST="unix:///var/run/docker.sock"
sudo ln -sf "$HOME/.colima/default/docker.sock" /var/run/docker.sock
```

To make this permanent, add the export to your shell config:

```bash
echo 'export DOCKER_HOST="unix:///var/run/docker.sock"' >> ~/.zshrc
```

See [colima#1067](https://github.com/abiosoft/colima/issues/1067) and [colima#997](https://github.com/abiosoft/colima/issues/997) for details.

## Self-Hosted Production

The Supabase CLI works with **any** PostgreSQL instance — no Supabase Cloud account required.

```bash
supabase db push --db-url "postgresql://user:pass@your-server:5432/dbname"
```

This applies the same migrations to your production database.

## Security

All tables have **Row Level Security (RLS) enabled** by default:

- The application connects as the `postgres` role, which has full access
- Supabase's `anon` and `authenticated` roles have **no policies** — meaning zero access via the PostgREST API
- This prevents accidental data exposure through Supabase's auto-generated REST API

For multi-user deployments, add per-user RLS policies (see comments in migration files).

## Stopping

```bash
supabase stop            # stop containers (data preserved)
supabase stop --no-backup  # stop and remove all data volumes
```

## Creating New Migrations

```bash
supabase migration new my_migration_name
```

Edit the generated file in `supabase/migrations/`, then apply with `supabase db push`.
