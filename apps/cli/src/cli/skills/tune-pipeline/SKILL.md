---
name: tune-pipeline
description: Help the user choose and tune a rag-facile preset for their use case.
triggers: ["tune", "optimize", "améliorer", "improve", "preset", "slower", "faster", "plus rapide", "plus lent", "performance", "qualité"]
---

# Skill: Tune Pipeline

You are helping the user pick the right preset and fine-tune their pipeline parameters.

## Step 1 — Understand their goal
Ask ONE of these depending on what they said:
- "Vous cherchez à améliorer la qualité des réponses, ou la vitesse ?"
- "Quel type de documents traitez-vous ? (PDF juridiques, articles, documentation technique...)"

## Step 2 — Read their current config
Call `get_ragfacile_config()`. Note the active preset and any overrides.

## Step 3 — Recommend a preset
| Use case | Recommended preset | Why |
|----------|--------------------|-----|
| General purpose | `balanced` | Good speed/quality trade-off |
| Best quality, speed secondary | `accurate` | Larger chunks, multi-query expansion |
| Fast prototyping | `fast` | Minimal reranking overhead |
| Legal / regulatory texts | `legal` | Tuned for long precise passages |
| HR / policy documents | `hr` | Public collections pre-configured |

## Step 4 — Explain the key levers
Only mention the parameters relevant to their symptom:
- **Speed slow?** → lower `top_k`, disable `reranking`, try `fast` preset
- **Answers vague?** → raise `top_n`, enable `multi_query` expansion
- **Missing context?** → raise `chunk_size` or `chunk_overlap`
- **Irrelevant results?** → lower `top_k`, raise reranking `top_n`

## Step 5 — Propose ONE concrete change
Always phrase as: "Je vous suggère de changer X en Y dans votre ragfacile.toml."
Wait for confirmation before suggesting the next change.

Use `get_docs("config")` to cite exact field names from the reference documentation.
