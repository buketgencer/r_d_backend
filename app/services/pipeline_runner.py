"""
Tek PDF – Çok Soru iş akışı
• preprocess_pdf()   → PDF’i ilk ve tek sefer işleyip FAISS indexler
• answer_question()  → FAISS’ten top-k chunk + prompt üret + (şimdilik) dummy/ GPT
"""

from pathlib import Path
from ..pipeline import (
    init_workspace, pdf_to_text, cid_cleaner,
    chunk_creator, faiss_creator,
    search_faiss_top_chunks, gpt_prompt_builder
)
from ..core.config import get_settings
from .sender import ask_llm              # yalnızca sender.py konuşur
import json, uuid

st = get_settings()

# ---------- 1) PDF’i işleyen tek seferlik adım ----------
def preprocess_pdf(pdf_path: Path) -> Path:
    """PDF → TXT → chunks → embedding → FAISS.  Tekrar çağrılmaz."""
    report_id = pdf_path.stem or f"r_{uuid.uuid4().hex[:6]}"
    ws_dir = Path(st.workspace_root) / report_id
    ws_dir.mkdir(parents=True, exist_ok=True)

    init_workspace.init_workspace(report_id, st.workspace_root)
    raw_txt   = pdf_to_text.pdf_to_txt(str(pdf_path), str(ws_dir))
    clean_txt = cid_cleaner.clean_txt(raw_txt, str(ws_dir))
    chunk_creator.create_chunks(clean_txt, str(ws_dir))
    faiss_creator.create_faiss_for_chunks(str(ws_dir), st.embed_model)
    return ws_dir


# ---------- 2) Her soru için çağrılır ----------
def answer_question(ws_dir: Path, question: str, method: str | None = None) -> dict:
    chunks = search_faiss_top_chunks.query(
        workspace_dir=str(ws_dir),
        question=question,
        top_k=st.topk,
        model_name=st.embed_model,
    )

    prompt = gpt_prompt_builder.build(question, method, chunks)

    # prompt’u disk’e kaydet; kontrol etmek istediğini söylemiştin
    prompt_file = ws_dir / f"prompt_{uuid.uuid4().hex[:6]}.txt"
    prompt_file.write_text(prompt, encoding="utf-8")

    # ---------- ŞİMDİLİK DUMMY CEVAP ----------
    dummy_answer = f"(dummy) {question[:60]}... → top-{st.topk} chunk’la analiz edildi."
    # GPT’ye geçmek istediğinde:
    #   answer = ask_llm(prompt)      # sadece bu satırı aç
    answer = dummy_answer

    return {
        "answer" : answer,
        "status" : "answer_found" if answer else "answer_notfound",
        "prompt_path": str(prompt_file)
    }
