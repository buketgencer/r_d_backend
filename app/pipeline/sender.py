#!/usr/bin/env python3
"""
sender.py – Prompt Runner as Importable Module
=============================================
Bu dosya, model pipeline'larından **doğrudan çağrılabilir** temiz bir
API (`send_answers`) sunar ve ayrıca CLI olarak da çalışır.

Görev
-----
1. ``<workspace>/PROMPTS/prompt_<id>.json`` dosyalarını okur.
2. Her prompt’u OpenAI ChatCompletion’a yollar.
3. Yanıtı ``<workspace>/ANSWERS/answer_<id>.json`` biçiminde kaydeder.

JSON Şeması → `{soru, yordam, cevap}`

Ana Fonksiyon – `send_answers`
------------------------------
```python
from sender import send_answers
send_answers()  # .env'deki WORKSPACE_ROOT & OPENAI_API_KEY kullanılır
```
Parametreler:
* **workspace**   : `Path | str | None` – Varsa belirtilen yol; yoksa
  `.env` içindeki `WORKSPACE_ROOT`.
* **model**       : OpenAI modeli (default `'gpt-4o-mini'`).
* **temperature** : Örnekleme sıcaklığı (default `0.0`).
* **delay**       : Her isteğin ardından saniye cinsinden bekleme (default `0.3`).
* **api_key**     : API anahtarı (CLI parametresi > fonksiyon argümanı >
  environment > `.env`).

Fonksiyon, her başarılı isteğin özetini içeren bir liste döndürür.

CLI Kullanımı
-------------
```bash
python sender.py                 # .env'deki WORKSPACE_ROOT kullanılır
python sender.py ./workspace     # yolu elle belirtin
```
Tüm CLI argümanları `send_answers` fonksiyonuna aynen aktarılır.

Gerekli Paketler
---------------
`pip install openai python-dotenv`
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

try:
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:
    raise SystemExit("❌  python-dotenv yüklü değil. `pip install python-dotenv`.")

try:
    import openai  # type: ignore
except ModuleNotFoundError:
    raise SystemExit("❌  openai paketi yüklü değil. `pip install openai`.")

# ---------------------------------------------------------------------------
# Ortam değişkenlerini (varsa) yükle
# ---------------------------------------------------------------------------

load_dotenv()  # proje kökündeki .env dosyasını okur

# ---------------------------------------------------------------------------
# Dahili yardımcılar
# ---------------------------------------------------------------------------

def _send_prompt(prompt_text: str, model: str, temperature: float) -> str:
    """Tek bir prompt’u OpenAI ChatCompletion’a gönder, cevabı döndür."""

    if "USER:" in prompt_text:
        system_part, user_part = prompt_text.split("USER:", 1)
        system_part = system_part.replace("SYSTEM:", "").strip()
        user_part = user_part.strip()
        messages = [
            {"role": "system", "content": system_part},
            {"role": "user",   "content": user_part},
        ]
    else:
        messages = [{"role": "user", "content": prompt_text}]

    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()

# ---------------------------------------------------------------------------
# Genel API – pipeline'lar burayı kullanacak
# ---------------------------------------------------------------------------

def send_answers(
    workspace: str | Path | None = None,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
    delay: float = 0.3,
    api_key: str | None = None,
) -> List[Dict[str, Any]]:
    """PROMPTS klasöründeki tüm prompt'ları işler ve ANSWERS'a yazar.

    Dönen liste: `[{"id": 1, "file": Path, "status": "ok"}, …]`
    """

    # API KEY öncelik sırası: arg > env var > .env
    openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
    print(f"[DEBUG] Kullanılan API key: {openai.api_key!r}")
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY bulunamadı (arg/env/.env)")

    # workspace belirle
    if workspace is None:
        workspace = os.getenv("WORKSPACE_ROOT")
        if workspace is None:
            raise RuntimeError("workspace parametresi verilmedi ve WORKSPACE_ROOT tanımlı değil")
    ws = Path(workspace).expanduser().resolve()
    if not ws.exists():
        raise FileNotFoundError(f"Workspace bulunamadı: {ws}")

    prompt_dir = ws / "PROMPTS"
    answer_dir = ws / "ANSWERS"
    answer_dir.mkdir(parents=True, exist_ok=True)

    prompt_files: List[Path] = sorted(
        prompt_dir.glob("prompt_*.json"),
        key=lambda p: int(p.stem.split("_")[1])
    )
    if not prompt_files:
        raise RuntimeError("PROMPTS klasöründe dosya yok; önce prompt üretin.")

    results: List[Dict[str, Any]] = []

    for pfile in prompt_files:
        qid = int(pfile.stem.split("_")[1])
        with pfile.open(encoding="utf-8") as f:
            pdata = json.load(f)

        try:
            answer_text = _send_prompt(pdata["prompt"], model, temperature)
            status = "ok"
        except Exception as exc:
            answer_text = str(exc)
            status = "error"

        out_json = {
            "soru": pdata.get("soru"),
            "yordam": pdata.get("yordam"),
            "cevap": answer_text,
        }
        out_path = answer_dir / f"answer_{qid}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(out_json, f, ensure_ascii=False, indent=2)

        results.append({"id": qid, "file": out_path, "status": status})
        time.sleep(delay)

    return results

# ---------------------------------------------------------------------------
# CLI – hala bağımsız çalışabilir, fakat simple wrapper
# ---------------------------------------------------------------------------

def _cli() -> None:
    ap = argparse.ArgumentParser(description="Send PROMPTS to GPT and store ANSWERS.")
    ap.add_argument("workspace", nargs="?", default=None,
                    help="Workspace root; boşsa .env'deki WORKSPACE_ROOT kullanılır")
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--api-key", default=None)
    args = ap.parse_args()

    try:
        send_answers(args.workspace, model=args.model, temperature=args.temperature,
                     delay=args.delay, api_key=args.api_key)
        print("✅  Görev tamamlandı.")
    except Exception as exc:
        sys.exit(f"❌  {exc}")

if __name__ == "__main__":  # pragma: no cover
    _cli()


'''
How to call :
from sender import send_answers

# Varsayılanlar: WORKSPACE_ROOT & OPENAI_API_KEY .env’den gelir
results = send_answers()               # tüm prompt-lar işlenir

# veya parametrelerle:
results = send_answers(
    workspace="workspace",
    model="gpt-4o-mini",
    temperature=0.0,
    delay=0.25
)
print(results)   # [{'id': 1, 'file': PosixPath('...'), 'status': 'ok'}, ...]


'''