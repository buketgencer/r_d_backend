"""
soru_yordam_embedder.py
────────────────────────
SORU-YORDAM listesini .txt dosyasından okuyup embed'ler ve FAISS index + metadata olarak kaydeder.
"""

import os, re, json
import numpy as np
import faiss
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from pathlib import Path

def vectorize_soru_yordam(txt_path: str, workspace_dir: str, model_name: str):
    """
    Parameters
    ----------
    txt_path : str
        .txt dosyasının yolu (soru-yordam formatlı)
    workspace_dir : str
        Örnek: workspace/rapor2023
    model_name : str
        Örnek: sentence-transformers/all-MiniLM-L6-v2
    """

    txt_path = str(Path(txt_path).expanduser().resolve())
    if not Path(txt_path).exists():
        print(f"⚠️ Dosya bulunamadı: {txt_path}")
        return


    out_dir = os.path.join(workspace_dir, "faiss")
    os.makedirs(out_dir, exist_ok=True)

    print(f"🧠 Model yükleniyor: {model_name}")
    model = SentenceTransformer(model_name)

    with open(txt_path, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    entries = []

    try:
        # Önce JSON dener
        json_data = json.loads(raw)
        for i, item in enumerate(json_data, 1):
            soru = item.get("soru", "").strip().replace("\n", " ")
            yordam = item.get("yordam", "").strip().replace("\n", " ")
            combined_text = f"SORU: {soru}" if not yordam else f"SORU: {soru}\nYORDAM: {yordam}"
            entries.append({
                "soru": soru,
                "yordam": yordam,
                "text": combined_text.strip()
            })
    except Exception:
        # Değilse eski blok-parsing yap
        blocks = raw.split("-" * 30)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            match = re.search(r"SORU\\s+(\\d+):\\s*(.*?)\\nYORDAM\\s+\\1:\\s*(.*)", block, re.DOTALL)
            if match:
                idx, soru, yordam = match.groups()
                soru = soru.strip().replace("\\n", " ")
                yordam = yordam.strip().replace("\\n", " ")
                combined_text = f"SORU: {soru}" if "[Boş]" in yordam else f"SORU: {soru}\nYORDAM: {yordam}"
                entries.append({
                    "id": int(idx),
                    "soru": soru,
                    "yordam": "" if "[Boş]" in yordam else yordam,
                    "text": combined_text.strip()
                })


    print(f"🔎 {len(entries)} soru-yordam çifti bulundu.")

    texts = [e["text"] for e in entries]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, os.path.join(out_dir, "faiss_soru_yordam.index"))
    with open(os.path.join(out_dir, "metadata_soru_yordam.json"), "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"✅ FAISS ve metadata kaydedildi: {out_dir}")