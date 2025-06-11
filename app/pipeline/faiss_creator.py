"""
faiss_creator.py
────────────────
Bir rapora ait chunk JSON'larını okuyarak her kategori (genel, ozel, mevzuat)
için embedding + FAISS index oluşturur.
"""

from __future__ import annotations
import os, json, faiss, numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

DATASETS = ["genel", "ozel", "mevzuat"]


# --------------------------------------------------
#  Ortak model‐yükleyici — .env → EMBED_MODEL okunur
# --------------------------------------------------
def _load_model(model_name: str | None = None) -> SentenceTransformer:
    if model_name is None:                                # .env belirtilmediyse
        model_name = os.getenv("EMBED_MODEL",
                               "sentence-transformers/all-MiniLM-L6-v2")
    return SentenceTransformer(model_name)


def create_faiss_for_chunks(workspace_dir: str,
                            model_name: str | None = None) -> None:
    """
    workspace_dir :  workspace/raporXXXX klasörü
    """
    chunk_root = os.path.join(workspace_dir, "chunks")
    output_dir = os.path.join(workspace_dir, "faiss")
    os.makedirs(output_dir, exist_ok=True)

    model = _load_model(model_name)

    for ds in DATASETS:
        print(f"\n🔧  {ds.upper()} için FAISS oluşturuluyor …")

        ds_folder  = os.path.join(chunk_root, ds)
        json_files = [f for f in os.listdir(ds_folder) if f.endswith(".json")]

        metadata: list[dict] = []
        texts:     list[str] = []

        for jf in json_files:
            with open(os.path.join(ds_folder, jf), encoding="utf-8") as f:
                data = json.load(f)
            metadata.append(data)
            texts.append(data["chunk_text"])

        if not texts:
            print(f"⚠️  Veri yok  →  {ds_folder}")
            continue

        # 🧠 Embedding
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        # 📈 FAISS index
        dim   = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

        # 📤 Kaydet
        faiss.write_index(index,
                          os.path.join(output_dir, f"faiss_{ds}.index"))
        with open(os.path.join(output_dir, f"metadata_{ds}.json"),
                  "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"✅  {ds} → index & metadata  →  {output_dir}")


# --------------------------------------------------
#  CLI test
# --------------------------------------------------
if __name__ == "__main__":
    create_faiss_for_chunks("workspace/rapor2023")