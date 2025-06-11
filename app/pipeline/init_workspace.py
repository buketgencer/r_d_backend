import os

def init_workspace(report_name: str, root="workspace"):
    """
    Bir rapor klasörü ve alt klasörlerini oluşturur.

    Parameters
    ----------
    report_name : str
        Örneğin 'rapor2023' gibi.
    root : str
        Ana çalışma dizini (varsayılan: 'workspace')
    """
    base_path = os.path.join(root, report_name)

    subdirs = [
        "raw_txt",
        "clean_txt",
        "chunks/genel",
        "chunks/ozel",
        "chunks/mevzuat",
        "faiss",
        "top10/genel",
        "top10/ozel",
        "top10/mevzuat",
        "expanded/genel",
        "expanded/ozel",
        "expanded/mevzuat",
    ]

    for sub in subdirs:
        full_path = os.path.join(base_path, sub)
        os.makedirs(full_path, exist_ok=True)

    print(f"📁 Workspace oluşturuldu → {base_path}")
    return base_path  # diğer fonksiyonlara iletmek için

# Elle kullanım:
if __name__ == "__main__":
    name = input("📌 Rapor adı girin (örnek: rapor2023): ").strip()
    init_workspace(name)