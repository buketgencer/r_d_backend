# pipeline ‘orkestratörü’
# Yüklenen PDF’i arka planda işler, prompt’u üretir, sender.post_to_outer_api() çağırır

"""
pipeline_runner.py
──────────────────
Upload edilen PDF’i işleyip GPT’ye gönderilecek prompt’u üretir
ve sonucu dış (açık) API’ye POST eder.

Bu dosya *yalnızca* orkestrasyon içerir; NLP-spesifik adımlar
app.pipeline paketindeki modüllerdedir.
"""

from __future__ import annotations
from pathlib import Path
from datetime import datetime
import traceback

from ..core.config import get_settings
from .sender import post_to_outer_api
# add state
from . import state         # pipeliner'ın başındaki import listesine

# NLP modülleri (eski script'ler → paket hâli)
from ..pipeline import (
    init_workspace,
    pdf_to_text,
    cid_cleaner,
    chunk_creator,
    faiss_creator,
    soru_yordam_embedder,
    search_faiss_top_chunks,
    expand_top10_chunks,
    gpt_prompt_builder,          # eski gpt_amacalismiyor.py
)


# --------------------------------------------------------------------------- #
#  Kaynak (sabit) dosyalar
# --------------------------------------------------------------------------- #
#   resources/  klasörü =  backend/app/pipeline/resources/
RESOURCES_DIR = Path(__file__).resolve().parents[1] / "pipeline" / "resources"
QUESTIONS_TXT = RESOURCES_DIR / "default_questions_and_yordams.txt"


# --------------------------------------------------------------------------- #
#  Ana fonksiyon – FastAPI BackgroundTasks içinde çağrılır
# --------------------------------------------------------------------------- #
def run_pipeline(
        pdf_path: Path,
        report_id: str,
        question_id: int,
        custom_question: str | None = None,
        custom_yordam:   str | None = None,
        job_id: str | None = None,          # ★ yeni parametre
) -> dict:
    """
    Parameters
    ----------
    pdf_path        : Kullanıcının yüklediği PDF’in geçici yolu
    report_id       : workspace alt klasör adı (örn: rapor2023)
    question_id     : 1-N, hazır sorulardan biri
    custom_question : Kullanıcı özel soru girerse
    custom_yordam   : Kullanıcı özel yordam girerse
    """
    t0 = datetime.utcnow()
    st = get_settings()                       # .env değerleri
    ws_dir = Path(st.workspace_root) / report_id

    try:
        # 1) workspace dizin ağacını oluştur
        init_workspace.init_workspace(report_id, st.workspace_root)

        # 2) hazır Soru-Yordam listesini embedle (her rapor için tek sefer yeter)
        soru_yordam_embedder.vectorize_soru_yordam(
            txt_path=str(QUESTIONS_TXT),
            workspace_dir=str(ws_dir),
            model_name=st.embed_model,
        )

        # 2.b) kullanıcı özel soru eklediyse embedle & FAISS'e ekle
        if custom_question:
            _inject_custom_question(
                custom_question, custom_yordam, ws_dir, st.embed_model
            )

        # 3) PDF → raw TXT
        raw_txt = pdf_to_text.pdf_to_txt(str(pdf_path), str(ws_dir))

        # 4) CID temizle
        clean_txt = cid_cleaner.clean_txt(raw_txt, str(ws_dir))

        # 5) Chunk’la
        chunk_creator.create_chunks(clean_txt, str(ws_dir))

        # 6) Chunk’ları embedle + FAISS index
        faiss_creator.create_faiss_for_chunks(str(ws_dir), st.embed_model)

        # 7) Soruya göre top-k chunk’ları bul
        search_faiss_top_chunks.ask_all(
            workspace_dir=str(ws_dir),
            top_k=st.topk,
            model_name=st.embed_model,
        )

        # 8) Chunk bağlamını genişlet
        expand_top10_chunks.expand_chunk(str(ws_dir))

        # 9) GPT’ye gönderilecek prompt’u hazırla
        prompt = gpt_prompt_builder.generate_prompt(question_id, str(ws_dir))

        # 9.b) oluşturulan promptu kaydet
        prompt_txt = ws_dir / f"prompt_question_{question_id}.txt"
        prompt_txt.write_text(prompt, encoding="utf-8")
        print(f"[INFO] Prompt saved to: {prompt_txt}")

        # 10) Sonucu dış API’ye POST et
        post_to_outer_api(prompt)

        status = "sent"
        error  = None

    except Exception as exc:                  # yakala & logla – API'yi çökertme
        status = "error"
        prompt = ""
        error  = f"{exc}\n{traceback.format_exc()}"
        print(f"[ERROR] pipeline failed: {exc}")

    duration = (datetime.utcnow() - t0).total_seconds()

    # ★ job_id verildiyse /status tablosunu güncelle
    if job_id:
        state.update(
            job_id,
            status=status,
            seconds=duration,
            error=error,
        )

    duration = (datetime.utcnow() - t0).total_seconds()

    return {
        "report_id":   report_id,
        "question_id": question_id,
        "status":      status,
        "seconds":     duration,
        "error":       error,
        "prompt":      prompt[:5000]  # çok uzun olabilir; kısalt
    }


# --------------------------------------------------------------------------- #
#  Yardımcı – özel soruyu embedleyip mevcut FAISS'e ekler
# --------------------------------------------------------------------------- #
def _inject_custom_question(
        soru: str,
        yordam: str | None,
        workspace_dir: Path,
        model_name: str,
) -> None:
    """
    Kullanıcı özel soru girdiğinde:
    • Geçici ID = 9999 (veya mevcut olmayan bir sayı) verilir.
    • Embed hesaplanıp soru_yordam FAISS'ine eklenir.
    Bu sayede aynı pipeline adımını tekrar modifiye etmeye gerek kalmaz.
    """
    if not soru:
        return

    tmp_txt = workspace_dir / "custom_soru.txt"
    content = f"SORU: {soru}\nYORDAM: {yordam or '[Boş]'}"
    tmp_txt.write_text(content, encoding="utf-8")

    soru_yordam_embedder.vectorize_soru_yordam(
        txt_path=str(tmp_txt),
        workspace_dir=str(workspace_dir),
        model_name=model_name,
    )
    # temp dosya temizlenebilir
    tmp_txt.unlink(missing_ok=True)

