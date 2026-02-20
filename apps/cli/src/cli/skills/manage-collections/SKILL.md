---
name: manage-collections
description: Discover, understand and enable/disable Albert API collections in ragfacile.toml. Use when the user asks about available datasets, wants to add a public collection, or wants to toggle collections on or off.
triggers: ["collections", "dataset public", "collection", "activer", "désactiver", "enable collection", "disable collection"]
---

# Skill: Manage Collections

You help the user discover available collections on the Albert API and configure
which ones are active in their RAG pipeline.

## Step 1 — Fetch available collections
Call `list_collections()` to retrieve all accessible collections.
Present the results clearly: highlight public collections (available to all users)
and the user's private ones separately.

## Step 2 — Explain what collections are
If the user seems unfamiliar, explain briefly:
- Collections are pre-indexed document sets stored on the Albert API
- Public collections include government datasets (service-public.fr, légifrance, etc.)
- Enabling a collection means the RAG pipeline will search it on every query
- Multiple collections can be active simultaneously

## Step 3 — Help them choose
Ask: "Quelles collections souhaitez-vous activer dans votre pipeline RAG ?"
Show the current active collections from `get_ragfacile_config()`.
Suggest relevant public ones based on their use case if known.

## Step 4 — Update the configuration
Once the user picks collection IDs, follow the update_config confirmation flow:
- Explain the change: "Je vais activer les collections X, Y, Z."
- Ask explicitly: "Puis-je mettre à jour storage.collections ? Le changement
  sera enregistré dans ragfacile.toml et committé dans git."
- On yes: call `update_config("storage.collections", "[id1, id2, ...]")`

## Rules
- Never modify collections without explicit user confirmation
- Always show current config before proposing changes
- Remind the user that session collections (uploaded files) are separate from
  public collections — both can be active at the same time
