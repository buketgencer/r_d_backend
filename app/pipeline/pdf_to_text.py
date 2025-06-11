import os
import pdfplumber

def pdf_to_txt(pdf_path: str, workspace_dir: str) -> str:
    """
    Parameters
    ----------
    pdf_path : str
        Kullanıcının yüklediği PDF dosyasının tam yolu
    workspace_dir : str
        workspace/rapor_adi klasörünün tam yolu (ör: "workspace/rapor2023")

    Returns
    -------
    str
        Üretilen .txt dosyasının tam yolu
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF bulunamadı: {pdf_path}")

    out_dir = os.path.join(workspace_dir, "raw_txt")
    os.makedirs(out_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    txt_path  = os.path.join(out_dir, base_name + ".txt")

    print(f"📰 PDF okunuyor → {os.path.basename(pdf_path)}")

    with pdfplumber.open(pdf_path) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
        full_text = "\n".join(pages)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(f"✅ TXT yazıldı → {txt_path}")
    return txt_path


# Elle kullanım örneği
if __name__ == "__main__":
    report_name = "rapor2023"
    pdf_file    = f"user_uploads/{report_name}.pdf"
    workspace   = f"workspace/{report_name}"
    pdf_to_txt(pdf_file, workspace)