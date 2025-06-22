#!/usr/bin/env python3
"""
pipeline_runner.py
==================
Tek bir komutla **uçtan uca** rapor‐işleme ve cevap üretme sürecini yönetir.

Aşamalar
--------
1. Workspace klasörlerini hazırla (`init_workspace`)
2. PDF → TXT (`pdf_to_text`)
3. CID temizliği (`cid_cleaner`)
4. Chunk oluşturma (`chunk_creator`)
5. Chunk embed + FAISS (`faiss_creator`)
6. Soru‑yordam embed + FAISS (`soru_yordam_embedder`)
7. Her soru için top‑k chunk bul (`search_faiss_top_chunks`)
8. Chunk’ları genişlet (`expand_top10_chunks`)
9. Prompt üret (`gpt_prompt_builder`)
10. (Opsiyonel) GPT’ye gönder, cevapları kaydet (`sender`)

Ortam Değişkenleri (.env)
-------------------------
OPENAI_API_KEY, WORKSPACE_ROOT, EMBED_MODEL, TOPK vb. değerler otomatik
okunur (python‑dotenv).
"""

from __future__ import annotations

import os
import uuid
import argparse
from pathlib import Path
from dotenv import load_dotenv

# ➊  Pipeline adımlarını içe aktar
from init_workspace import init_workspace
from pdf_to_text import pdf_to_txt
from cid_cleaner import clean_txt
from chunk_creator import create_chunks
from faiss_creator import create_faiss_for_chunks
from soru_yordam_embedder import vectorize_soru_yordam
from search_faiss_top_chunks import ask_all
from expand_top10_chunks import expand_chunk
from gpt_prompt_builder import generate_all_prompts
from sender import send_answers

# --------------------------------------------------
#  Ortam değişkenlerini yükle (.env dosyası)
# --------------------------------------------------

load_dotenv()  # proje kökündeki .env okunur

# --------------------------------------------------
#  Ana çalışma fonksiyonu
# --------------------------------------------------

def run_pipeline(
    *,
    pdf_path: str | Path,
    questions_path: str | Path,
    report_id: str | None = None,
    send_to_gpt: bool = True,
    embed_model: str | None = None,
    top_k: int | None = None,
) -> Path:
    """Tüm adımları sırayla çalıştırır ve workspace yolunu döndürür."""

    # ---- Ayarlar (.env + parametre) ----------------
    workspace_root = Path(os.getenv("WORKSPACE_ROOT", "workspace")).expanduser()
    embed_model = embed_model or os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    top_k = top_k or int(os.getenv("TOPK", "10"))

    # ---- Workspace -------------------------------
    report_id = report_id or Path(pdf_path).stem or f"r_{uuid.uuid4().hex[:6]}"
    workspace_dir = workspace_root / report_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # 1. klasör yapısı
    init_workspace(report_id, str(workspace_root))

    # 2. PDF → TXT
    txt_path = pdf_to_txt(str(pdf_path), str(workspace_dir))

    # 3. CID fix
    clean_path = clean_txt(txt_path, str(workspace_dir))

    # 4. Chunk oluştur
    create_chunks(clean_path, str(workspace_dir))

    # 5. Chunk embed → FAISS
    create_faiss_for_chunks(str(workspace_dir), embed_model)

    # 6. Soru‑yordam embed → FAISS
    vectorize_soru_yordam(str(questions_path), str(workspace_dir), embed_model)

    # 7. Top‑k chunk bul
    ask_all(str(workspace_dir), top_k=top_k, model_name=embed_model)

    # 8. Chunk genişlet
    expand_chunk(str(workspace_dir))

    # 9. Prompt üret
    generate_all_prompts(workspace_dir)

    # 10. Cevap al (isteğe bağlı)
    #if send_to_gpt:
        #send_answers(workspace_dir)

    print("🎉 Pipeline tamamlandı →", workspace_dir)
    return workspace_dir

# --------------------------------------------------
#  CLI sarıcı
# --------------------------------------------------

def _cli() -> None:
    p = argparse.ArgumentParser(description="Tek komutla rapor pipeline'ı çalıştır.")
    p.add_argument("pdf", help="Kaynak PDF dosyası")
    p.add_argument("questions", help="Soru‑yordam .txt veya .json dosyası")
    p.add_argument("--id", dest="report_id", default=None, help="Rapor kimliği (klasör adı)")
    p.add_argument("--no-gpt", action="store_true", help="GPT'ye göndermeden dur")
    p.add_argument("--model", dest="embed_model", default=None, help="Sentence‑Transformers modeli")
    p.add_argument("--topk", dest="top_k", type=int, default=None, help="Top‑k chunk sayısı")
    args = p.parse_args()

    run_pipeline(
        pdf_path=args.pdf,
        questions_path=args.questions,
        report_id=args.report_id,
        send_to_gpt=not args.no_gpt,
        embed_model=args.embed_model,
        top_k=args.top_k,
    )

if __name__ == "__main__":  # pragma: no cover
    _cli()


'''
How to use this script:
from pdf_to_text import pdf_to_txt
pdf_to_txt("user_uploads/rapor2024.pdf", "workspace/rapor2024")

'''