import logging, os
from typing import Any
import httpx

logger = logging.getLogger(__name__)

def send_accepted_webhook(payload: dict[str, Any]) -> None:
    url = os.environ.get("WEBHOOK_URL")
    if not url:
        return
    try:
        httpx.post(url, json=payload, timeout=5.0)
    except Exception:
        logger.exception("Webhook delivery to %s failed", url)