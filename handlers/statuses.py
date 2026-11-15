import logging

logger = logging.getLogger(__name__)


def message_status_handler(status: dict):
    logger.info(
        "WhatsApp message status updated",
        extra={
            "message_id": status.get("id"),
            "status": status.get("status"),
            "recipient_id": status.get("recipient_id"),
        },
    )