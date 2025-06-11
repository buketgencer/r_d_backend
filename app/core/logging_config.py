# (basit log ayarı – opsiyonel)
# app/core/logging_config.py
import logging, sys, pathlib, datetime

LOG_DIR = pathlib.Path("logs")
LOG_DIR.mkdir(exist_ok=True)

stamp = datetime.datetime.utcnow().strftime("%Y%m%d")
log_path = LOG_DIR / f"backend_{stamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),      # konsola
        logging.FileHandler(log_path, encoding="utf-8"),  # dosyaya
    ],
)
