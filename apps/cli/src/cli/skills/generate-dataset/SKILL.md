---
name: generate-dataset
description: Guide the user through generating a synthetic Q&A evaluation dataset from their documents using the Albert API. Use when the user wants to evaluate their RAG pipeline or create test data.
triggers: ["generate dataset", "golden dataset", "evaluation dataset", "créer dataset", "générer dataset", "eval", "évaluation", "test data"]
---

# Skill: Generate Dataset

You guide the user through generating a synthetic Q&A evaluation dataset from
their documents. This dataset is used to measure RAG pipeline quality.

## What is a golden dataset?
A golden dataset is a set of question-answer pairs generated from the user's
actual documents. It lets them measure how well their RAG pipeline retrieves
the right information. More Q&A pairs = more reliable evaluation.

## Step 1 — Check the workspace
Call `get_ragfacile_config()` to confirm the workspace is set up correctly.
The user needs an Albert API key configured to use the Albert provider.

## Step 2 — Find the source documents
Ask: "Où sont vos documents source ? (chemin vers le dossier, ex: ./docs)"
The directory should contain PDF, Markdown, or HTML files.
Verify the path exists and explain: "Je vais utiliser ces documents pour
générer des paires question-réponse via l'API Albert."

## Step 3 — Set the output file
Suggest a sensible default: `golden_dataset.jsonl` in the workspace root.
Ask if they want a different name or location.

## Step 4 — Choose the number of questions
Recommend 20 questions for a first run (fast, gives a quick signal).
Explain: "Plus il y a de questions, plus l'évaluation est précise,
mais la génération prend plus de temps (~1 min pour 20 questions)."
Max: 100 questions.

## Step 5 — Confirm and run
Summarise before starting:
- Source: <docs_path>
- Output: <output_file>
- Questions: <num>
- Provider: Albert API
- Duration: ~<estimate> minutes

Ask: "Puis-je lancer la génération ?"
On yes: call `run_generate_dataset(docs_path, output_file, num_questions)`.
Warn the user it may take a few minutes and they should not close the terminal.

## Step 6 — Explain next steps
On success, explain how to use the dataset:
"Votre dataset est prêt. Pour évaluer votre pipeline RAG :
  rag-facile eval --dataset golden_dataset.jsonl
Cela mesurera la précision de votre pipeline sur vos propres documents."

## Rules
- Always confirm docs path, output file and question count before calling run_generate_dataset
- Never call run_generate_dataset without explicit user confirmation
- If generation fails, show the error and suggest checking API key and docs format
- Remind users that only PDF, Markdown and HTML files are supported
