"""
Unit tests for Azure Service Bus producer integration in app/queue.py.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.queue import send_job_message
from app.config import settings


@pytest.mark.asyncio
async def test_send_job_message_when_no_connection_string():
    with patch.object(settings, "service_bus_connection_string", ""):
        result = await send_job_message("job-123", "generate_report")
        assert result is False


@pytest.mark.asyncio
async def test_send_job_message_success():
    with patch.object(
        settings,
        "service_bus_connection_string",
        "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=testkey=",
    ):
        with patch("app.queue.ServiceBusClient") as mock_sb_class:
            mock_sender = AsyncMock()
            mock_sender_cm = MagicMock()
            mock_sender_cm.__aenter__ = AsyncMock(return_value=mock_sender)
            mock_sender_cm.__aexit__ = AsyncMock(return_value=None)

            mock_client = MagicMock()
            mock_client.get_queue_sender.return_value = mock_sender_cm

            mock_client_cm = MagicMock()
            mock_client_cm.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cm.__aexit__ = AsyncMock(return_value=None)

            mock_sb_class.from_connection_string.return_value = mock_client_cm

            result = await send_job_message("job-123", "generate_report")
            assert result is True
            mock_sender.send_messages.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_job_message_handles_exception_gracefully():
    with patch.object(
        settings,
        "service_bus_connection_string",
        "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=testkey=",
    ):
        with patch("app.queue.ServiceBusClient") as mock_sb_class:
            mock_sb_class.from_connection_string.side_effect = Exception("Service Bus unreachable")

            result = await send_job_message("job-123", "generate_report")
            assert result is False
