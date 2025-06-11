# (gpt_amacalismiyor.py yeniden adlandı)
import json
from pathlib import Path
from textwrap import dedent

"""
Prompt Generator for R&D Center Evaluation
-----------------------------------------
• Reads **soru‑yordam** metadata and the **expanded** top‑10 chunk files.
• Builds a single prompt that ChatGPT can answer *strictly* from the chunks.
• Indices (1…N) are only for citation; chunks are not ranked globally.
• The answer instructions ask the model to evaluate each criterion in the *yordam*,
  marking which points are **karşılanan** and which are **eksik**, with suggestions.

Usage
~~~~~
>>> python generate_prompt.py 3
(or call `generate_prompt(3)` inside another script)

The section that actually sends the prompt to OpenAI is commented‑out; remove the
comment to activate in production.
"""

# ---------------------------------------------------------------------------
# Configuration — adjust paths for your environment
# ---------------------------------------------------------------------------

DATASETS          = ["genel", "ozel", "mevzuat"]  # search folders
MIN_CHUNK_CHARS   = 30   # ignore very short/noisy snippets
MAX_TOTAL_CHUNKS  = 30   # hard cap in final prompt

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _load_questions(meta_path: Path):
    """Return a dict {id: record} from the metadata file."""
    with meta_path.open("r", encoding="utf-8") as f:
        return {item["id"]: item for item in json.load(f)}


def _load_chunks(dataset: str, question_id: int, chunk_base: Path):
    fname = chunk_base / dataset / f"soru{question_id}_top10.json"
    """Load expanded top‑10 file for a dataset/question and filter decent snippets."""
    if not fname.exists():
        return []
    with fname.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    good = []
    for item in raw:
        text = (item.get("chunk_text", "") or "").strip()
        if len(text) >= MIN_CHUNK_CHARS:
            good.append({
                "text": text,
                "dataset": dataset,
                # keep score if present — may help future ranking tweaks
                "score": item.get("score", None)
            })
    return good


def generate_prompt(question_id: int, workspace_dir: str, total_chunks: int = MAX_TOTAL_CHUNKS) -> str:
    question_path = Path(workspace_dir) / "faiss" / "metadata_soru_yordam.json"
    chunk_base    = Path(workspace_dir) / "expanded"
    """Return the complete evaluation prompt for the given *question_id*."""

    # --- fetch soru & yordam ------------------------------------------------
    questions = _load_questions(question_path)
    if question_id not in questions:
        raise ValueError(f"Question id {question_id} not found in metadata")

    meta   = questions[question_id]
    soru   = meta["soru"].strip()
    yordam = meta["yordam"].strip()

    # --- gather chunks from all datasets ------------------------------------
    chunks = []
    for ds in DATASETS:
        chunks.extend(_load_chunks(ds, question_id, chunk_base))

    # cap (preserve original order – no global ranking available)
    chunks = chunks[:total_chunks]

    # --- build text sections ------------------------------------------------
    prompt_lines = []
    index = 1
    for ds in DATASETS:
        ds_chunks = [c for c in chunks if c["dataset"] == ds]
        if not ds_chunks:
            continue
        prompt_lines.append(f"{{<{ds}>={ds}}}")
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
# CLI helper (python generate_prompt.py <id>)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse, textwrap, sys

    parser = argparse.ArgumentParser(description="Generate evaluation prompt for a given question ID.")
    parser.add_argument("question_id", type=int, help="ID of the question to build the prompt for")
    args = parser.parse_args()

    try:
        prompt_str = generate_prompt(args.question_id)
    except Exception as exc:
        sys.exit(f"Error: {exc}")

    print("\n" + "=" * 88 + "\n")
    print(prompt_str)
    print("\n" + "=" * 88 + "\n")

    # ----------------------------------------------------------------------
    # SEND TO GPT (disabled) — uncomment when ready for production
    # ----------------------------------------------------------------------
    # import openai
    # response = openai.ChatCompletion.create(
    #     model="gpt-4o-mini",  # ya da tercih ettiğiniz model
    #     messages=[
    #         {"role": "system", "content": prompt_str.split("USER:")[0].strip()},
    #         {"role": "user",   "content": prompt_str.split("USER:")[1].strip()}
    #     ],
    #     temperature=0.0,
    # )
    # print(response.choices[0].message.content)