# dış API’ye POST
# requests.post() ile internete açık API’ye sonucu yollar

import requests
from ..core.config import get_settings

def post_to_outer_api(prompt: str) -> None:
    st = get_settings()
    headers = {"Authorization": f"Bearer {st.outer_api_token}"}
    try:
        resp = requests.post(
            st.outer_api_url,
            json={"prompt": prompt},
            headers=headers,
            timeout=60 # 60 saniye zaman asimi
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[WARN] Outer API post failed: {exc}") # hata durumunda uyarı ver
