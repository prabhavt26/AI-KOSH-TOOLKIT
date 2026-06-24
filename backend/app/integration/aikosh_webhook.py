import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AIKoshWebhook:
    async def post_quality_metadata(self, webhook_url: str, payload: Dict[str, Any]) -> bool:
        """POSTs assessment results back to the AIKosh platform webhook."""
        if not webhook_url:
            logger.warning("No webhook URL provided. Skipping webhook post.")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()
                logger.info(f"Successfully posted quality metadata to {webhook_url}")
                return True
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error posting webhook: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Failed to post quality metadata to webhook: {e}")
        return False

    def post_quality_metadata_sync(self, webhook_url: str, payload: Dict[str, Any]) -> bool:
        """POSTs assessment results back to the AIKosh platform webhook synchronously."""
        if not webhook_url:
            logger.warning("No webhook URL provided. Skipping webhook post.")
            return False
            
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(webhook_url, json=payload)
                response.raise_for_status()
                logger.info(f"Successfully posted quality metadata synchronously to {webhook_url}")
                return True
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error posting webhook: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Failed to post quality metadata synchronously to webhook: {e}")
        return False

webhook = AIKoshWebhook()

