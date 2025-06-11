"""
chunk_creator.py
────────────────
Bir temizlenmiş .txt dosyasını 3 farklı kategoriye göre cümle cümle bölerek chunk'lar üretir.
Her chunk JSON olarak kaydedilir.
"""

import os
import re
import json
from tqdm import tqdm

CHUNK_CONFIG = {
    "genel":   {"size": 5, "overlap": 3},
    "ozel":    {"size": 2, "overlap": 1},
    "mevzuat": {"size": 6, "overlap": 4}
}

HEADER_PATTERN = re.compile(r"^\d+(\.\d+)*(\s+|$)")

def smart_sentence_split(text):
    text = text.replace('\n', ' ')
    text = re.sub(r'(?<=\d)\.(?=\d)', '__DOT__', text)
    text = re.sub(r'\b([A-Za-zÇĞİÖŞÜçğıöşü]{1,4})\.', r'\1__DOT__', text)

    raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ])', text)
    cleaned = []

    for s in raw_sentences:
        s = s.replace('__DOT__', '.').strip()
        if HEADER_PATTERN.match(s) and len(s.split()) <= 10:
            cleaned.append(s)
        elif len(s) > 10:
            cleaned.append(s)

    return cleaned

def chunk_sentences(sentences, size, overlap):
    chunks = []
    for i in range(0, len(sentences), size - overlap):
        chunk = sentences[i:i + size]
        if chunk:
            chunks.append(chunk)
    return chunks

def create_chunks(clean_txt_path: str, workspace_dir: str) -> str:
    """
    Parameters
    ----------
    clean_txt_path : str
        CID'den temizlenmiş .txt dosyasının tam yolu
    workspace_dir : str
        Bu rapora ait ana klasör (ör: workspace/rapor2023)

    Returns
    -------
    str : Üretilen chunk klasörünün tam yolu
    """
    if not os.path.isfile(clean_txt_path):
        raise FileNotFoundError(clean_txt_path)

    with open(clean_txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    base_name    = os.path.splitext(os.path.basename(clean_txt_path))[0]
    sentences    = smart_sentence_split(text)
    chunk_root   = os.path.join(workspace_dir, "chunks")
    os.makedirs(chunk_root, exist_ok=True)

    for category, config in CHUNK_CONFIG.items():
        cat_dir = os.path.join(chunk_root, category)
        os.makedirs(cat_dir, exist_ok=True)

        chunks = chunk_sentences(sentences, config["size"], config["overlap"])

        for i, chunk in enumerate(chunks):
            chunk_text = " ".join(chunk)
            metadata = {
                "source_file": os.path.basename(clean_txt_path),
                "category": category,
                "chunk_index": i + 1,
                "chunk_text": chunk_text,
                "char_len": len(chunk_text),
                "sentence_count": len(chunk)
            }

            file_path = os.path.join(cat_dir, f"{category}_chunk_{i+1}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"✅ Chunklar üretildi → {chunk_root}")
    return chunk_root


# Test örneği
if __name__ == "__main__":
    report_name = "rapor2023"
    clean_txt   = f"workspace/{report_name}/clean_txt/{report_name}.txt"
    workspace   = f"workspace/{report_name}"
    create_chunks(clean_txt, workspace)