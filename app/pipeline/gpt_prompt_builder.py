#!/usr/bin/env python3
"""
Prompt Generator for R&D Center Evaluation
-----------------------------------------
• Reads **soru‑yordam** metadata and the **expanded** top‑10 chunk files.
• Builds a single prompt that ChatGPT can answer *strictly* from the chunks.
• Indices (1…N) are only for citation; chunks are not ranked globally.

NEW (June 2025)
~~~~~~~~~~~~~~~~
Instead of sending the prompt to OpenAI, the script now creates one JSON
file per question under ``<workspace>/PROMPTS``.  Each file is named
``prompt_<id>.json`` and contains three keys:

    ``{"soru": "…", "yordam": "…", "prompt": "…"}``

Run from the project root:

>>> python generate_prompt.py /path/to/workspace

All other behaviour (chunk selection, prompt formatting, etc.) is
unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Any

# ---------------------------------------------------------------------------
# Configuration — adjust paths for your environment
# ---------------------------------------------------------------------------

DATASETS: List[str] = ["genel", "ozel", "mevzuat"]  # search folders
MIN_CHUNK_CHARS = 30   # ignore very short/noisy snippets
MAX_TOTAL_CHUNKS = 30   # hard cap in final prompt

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _load_questions(meta_path: Path) -> Dict[int, Dict[str, Any]]:
    """Return a dict {id: record} from the metadata file."""
    with meta_path.open("r", encoding="utf-8") as f:
        return {int(item["id"]): item for item in json.load(f)}


def _load_chunks(dataset: str, question_id: int, chunk_base: Path) -> List[Dict[str, Any]]:
    """Load expanded top‑10 file for a dataset/question and filter decent snippets."""
    fname = chunk_base / dataset / f"soru{question_id}_top10.json"
    if not fname.exists():
        return []

    with fname.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    good: List[Dict[str, Any]] = []
    for item in raw:
        text = (item.get("chunk_text", "") or "").strip()
        if len(text) >= MIN_CHUNK_CHARS:
            good.append({
                "text": text,
                "dataset": dataset,
                "score": item.get("score")
            })
    return good


def generate_prompt(question_id: int, workspace_dir: Path, total_chunks: int = MAX_TOTAL_CHUNKS) -> str:
    """Return the complete evaluation prompt for the given *question_id*."""

    question_path = workspace_dir / "faiss" / "metadata_soru_yordam.json"
    chunk_base = workspace_dir / "expanded"

    # --- fetch soru & yordam ------------------------------------------------
    questions = _load_questions(question_path)
    if question_id not in questions:
        raise ValueError(f"Question id {question_id} not found in metadata")

    meta = questions[question_id]
    soru = meta["soru"].strip()
    yordam = meta["yordam"].strip()

    # --- gather chunks from all datasets ------------------------------------
    chunks: List[Dict[str, Any]] = []
    for ds in DATASETS:
        chunks.extend(_load_chunks(ds, question_id, chunk_base))

    # cap (preserve original order – no global ranking available)
    chunks = chunks[:total_chunks]

    # --- build text sections ------------------------------------------------
    prompt_lines: List[str] = []
    index = 1
    for ds in DATASETS:
        ds_chunks = [c for c in chunks if c["dataset"] == ds]
        if not ds_chunks:
            continue
        prompt_lines.append(f"{{<{ds}>= {ds}}}")
        for c in ds_chunks:
            prompt_lines.append(f"({index}) {c['text']}")
            c["index"] = index
            index += 1

    section_text = "\n".join(prompt_lines)

    # --- craft final prompt --------------------------------------------------
    prompt = dedent(f"""
    SYSTEM:
    You are an expert evaluator of R‑D centre activity reports.
    You must answer strictly and **only** from the chunks the user provides.
    If the chunks don’t contain enough evidence, reply exactly with
    “Bilgi bulunamadı.” – nothing else.

    USER:
    ### SORU {question_id}
    {soru}

    ### YORDAM {question_id}
    {yordam}

    ### KAYNAK METİNLER
    Aşağıda soruyla ilişkili en fazla {index-1} metin parçası bulunuyor (sırasız).
    **Tamamını okuyun** ve ardından **özlü** bir yanıt verin. Yanıtınız:
    • Yordamda listelenen *her* kriteri değerlendirir;
      – Karşılanan hususları kısaca onaylar,
      – Eksik hususları belirtir ve gerekirse öneri sunar.
    • Dayandığınız parçaların numaralarını **[3]**, **[7]** gibi gösterir.
    • Türkçe yazılır.
    Eğer uygun parça yoksa yalnızca “Bilgi bulunamadı.” yazın.

    {section_text}
    """).strip()

    return prompt

# ---------------------------------------------------------------------------
# Bulk generation helper
# ---------------------------------------------------------------------------

def generate_all_prompts(workspace_dir: Path) -> None:
    """Generate and save prompt files for **all** questions in the workspace."""

    meta_path = workspace_dir / "faiss" / "metadata_soru_yordam.json"
    questions = _load_questions(meta_path)

    out_dir = workspace_dir / "PROMPTS"
    out_dir.mkdir(parents=True, exist_ok=True)

    for qid in sorted(questions):
        prompt_text = generate_prompt(qid, workspace_dir)
        record = questions[qid]
        out_json = {
            "soru": record["soru"].strip(),
            "yordam": record["yordam"].strip(),
            "prompt": prompt_text
        }
        outfile = out_dir / f"prompt_{qid}.json"
        with outfile.open("w", encoding="utf-8") as f:
            json.dump(out_json, f, ensure_ascii=False, indent=2)
        print(f"✓ saved {outfile.relative_to(workspace_dir)}")

# ---------------------------------------------------------------------------
# CLI entry‑point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate evaluation prompts for ALL questions.")
    parser.add_argument("workspace", type=str, help="Root of the project workspace (contains faiss/, expanded/ etc.)")
    args = parser.parse_args()

    root = Path(args.workspace).expanduser().resolve()
    if not root.exists():
        sys.exit(f"Error: workspace directory '{root}' does not exist")

    try:
        generate_all_prompts(root)
    except Exception as exc:
        sys.exit(f"Error: {exc}")
