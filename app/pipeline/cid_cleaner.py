import os
import re

# —— CID → karakter eşlemeleri
CID_MAP = {
    'cid:62':  'şt',
    'cid:63':  'me',
    'cid:64':  'er',
    'cid:80':  'ti',
    'cid:82':  'f',
    'cid:85':  'ğ',
    'cid:88':  'lı',
    'cid:89':  'şi',
    'cid:90':  'ik',
    'cid:93':  'tf',
    'cid:94':  'tt',
    'cid:95':  'is',
    'cid:97':  'tf',
    'cid:99':  'tt',
    'cid:101': 'tt',
    'cid:102': 'tf',
    'cid:109': 'ş',
    'cid:110': 'ğ',
}

CID_PATTERN = re.compile(r'\(cid:\d+\)')

def fix_cids(text: str) -> str:
    for cid, repl in CID_MAP.items():
        text = text.replace(f"({cid})", repl)
    return CID_PATTERN.sub("", text)

def clean_txt(raw_txt_path: str, workspace_dir: str) -> str:
    """
    Parameters
    ----------
    raw_txt_path : str
        pdf_to_txt'tan gelen .txt dosyasının yolu
    workspace_dir : str
        workspace/rapor_adi klasörü

    Returns
    -------
    str
        Temizlenmiş .txt dosyasının tam yolu
    """
    if not os.path.isfile(raw_txt_path):
        raise FileNotFoundError(raw_txt_path)

    out_dir = os.path.join(workspace_dir, "clean_txt")
    os.makedirs(out_dir, exist_ok=True)

    base_name  = os.path.basename(raw_txt_path)
    clean_path = os.path.join(out_dir, base_name)

    with open(raw_txt_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    cleaned = fix_cids(raw_text)

    with open(clean_path, "w", encoding="utf-8") as f:
        f.write(cleaned)

    print(f"🧹 CID temizlendi → {clean_path}")
    return clean_path


# Elle kullanım
if __name__ == "__main__":
    report_name = "rapor2023"
    raw_txt     = f"workspace/{report_name}/raw_txt/{report_name}.txt"
    workspace   = f"workspace/{report_name}"
    clean_txt(raw_txt, workspace)