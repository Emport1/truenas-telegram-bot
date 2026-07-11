import logging

from .bot import build_application
from .config import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)

build_application(Settings.from_env()).run_polling(allowed_updates=["message"], drop_pending_updates=True)

