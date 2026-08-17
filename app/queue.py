"""
Azure Service Bus queue integration (Producer).

Provides `send_job_message` to enqueue jobs for worker processing.
Gracefully handles missing connection strings or transient failures
so the HTTP request does not fail if the queue is unreachable.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage

from app.config import settings

logger = logging.getLogger(__name__)


async def send_job_message(job_id: str, job_type: str) -> bool:
    """
    Publish a job message to the Azure Service Bus queue.

    Returns True if successfully sent, False otherwise.
    Never raises an exception — logs any error and returns False.
    """
    conn_str = settings.service_bus_connection_string
    if not conn_str:
        logger.debug("Service Bus connection string not configured; skipping queue message.")
        return False

    queue_name = settings.service_bus_queue_name
    payload = json.dumps({"job_id": job_id, "job_type": job_type})
    message = ServiceBusMessage(payload)

    try:
        async with ServiceBusClient.from_connection_string(conn_str) as client:
            async with client.get_queue_sender(queue_name=queue_name) as sender:
                await sender.send_messages(message)
                logger.info(f"Published job {job_id} ({job_type}) to queue '{queue_name}'.")
                return True
    except Exception as exc:
        logger.error(f"Failed to publish job {job_id} to Service Bus queue '{queue_name}': {exc}", exc_info=True)
        return False
