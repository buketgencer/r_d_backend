"""
Belirtilen workspace’teki FAISS indekslerinde arama yapar ve her soru için
en alakalı top-k chunk’ı üretir.  ask_all() fonksiyonu diğer script’lerden
çağrılabilir; istersek CLI ile de hâlâ çalıştırabiliriz.
"""

from __future__ import annotations
import os, json, faiss, numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

# ---------------------------------------------
#  Ortak model‐yükleyici (.env → EMBED_MODEL)
# ---------------------------------------------
def _load_model(model_name: str | None = None) -> SentenceTransformer:
    if model_name is None:
        model_name = os.getenv("EMBED_MODEL",
                               "sentence-transformers/all-MiniLM-L6-v2")
    return SentenceTransformer(model_name)


DATASETS = {
    "genel":   {"index": "faiss_genel.index",   "meta": "metadata_genel.json"},
    "mevzuat": {"index": "faiss_mevzuat.index", "meta": "metadata_mevzuat.json"},
    "ozel":    {"index": "faiss_ozel.index",    "meta": "metadata_ozel.json"},
}


# ------------------------------------------------------------------
#  Ana fonksiyon – pipeline içinden çağırmak için
# ------------------------------------------------------------------
def ask_all(workspace_dir: str,
            top_k: int = 10,
            model_name: str | None = None) -> None:
    """
    workspace_dir :  workspace/raporXXXX
    top_k         :  her soru için döndürülecek chunk sayısı
    model_name    :  Sentence-Transformers model adı (opsiyonel)
    """
    faiss_dir = os.path.join(workspace_dir, "faiss")
    topk_dir  = os.path.join(workspace_dir, "top10")
    os.makedirs(topk_dir, exist_ok=True)

    model = _load_model(model_name)

    print(f"\n🔍  FAISS indeksleri arama için yükleniyor …")

    # ❓ Soru-Yordam dosyası
    soru_path = os.path.join(faiss_dir, "metadata_soru_yordam.json")
    with open(soru_path, encoding="utf-8") as f:
        sorular = json.load(f)

    def search_faiss(query: str, faiss_index, k: int):
        emb = model.encode([query], convert_to_numpy=True,
                           normalize_embeddings=True)
        _, idxs = faiss_index.search(emb, k)
        return idxs[0]

    # 🔄 dataset bazlı döngü
    for ds, files in DATASETS.items():
        print(f"\n🔍  DATASET  →  {ds.upper()}")
        out_dir = os.path.join(topk_dir, ds)
        os.makedirs(out_dir, exist_ok=True)

        index   = faiss.read_index(os.path.join(faiss_dir, files["index"]))
        with open(os.path.join(faiss_dir, files["meta"]), encoding="utf-8") as f:
            metadata = json.load(f)

        for i, soru in enumerate(tqdm(sorular, desc=f"{ds} sorular"), 1):
            qid = soru.get("id", i)
            qtext = soru.get("text") or soru.get("soru") or ""
            top_idxs   = search_faiss(qtext, index, top_k)

            results = []
            for rank, idx in enumerate(top_idxs, 1):
                entry = metadata[idx]
                results.append({
                    "rank":           rank,
                    "index":          int(idx),
                    "chunk_text":     entry["chunk_text"],
                    "source_file":    entry.get("source_file"),
                    "char_len":       int(entry.get("char_len", 0)),
                    "sentence_count": int(entry.get("sentence_count", 0)),
                })

            # ✅ Kaydet
            with open(os.path.join(out_dir, f"soru{qid}_top{top_k}.json"),
                      "w", encoding="utf-8") as jf:
                json.dump(results, jf, ensure_ascii=False, indent=2)

            if qid == 1:                          # küçük örnek çıktı
                print(f"   • soru{qid}: {results[0]['chunk_text'][:100]}…")

    print("\n✅  Tüm sorular için top-k sonuçlar kaydedildi.")


# ------------------------------------------------------------------
#  Stand-alone CLI
# ------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace", help="workspace/raporXXXX")
    ap.add_argument("--k", type=int, default=10, help="top-k")
    ap.add_argument("--model", default=None,
                    help="Sentence-Transformers model adı")
    args = ap.parse_args()
    ask_all(args.workspace, top_k=args.k, model_name=args.model)