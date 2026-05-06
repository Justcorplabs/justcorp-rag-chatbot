from typing import Dict, Any

import requests

from app.config import settings


class WhatsAppClient:
    """
    Client for sending WhatsApp messages using Meta WhatsApp Cloud API.
    """

    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID

        self.base_url = (
            f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"
        )

    def is_configured(self) -> bool:
        """
        Check if WhatsApp credentials are available.
        """

        return bool(self.access_token and self.phone_number_id)

    def send_text_message(self, to_phone_number: str, message_text: str) -> Dict[str, Any]:
        """
        Send a text message to a WhatsApp user.

        Args:
            to_phone_number: Recipient phone number in international format.
            message_text: Message body to send.

        Returns:
            Meta API JSON response.
        """

        if not self.is_configured():
            raise ValueError(
                "WhatsApp client is not configured. Check WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID."
            )

        if not to_phone_number:
            raise ValueError("Recipient phone number is required.")

        if not message_text:
            raise ValueError("Message text is required.")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text,
            },
        }

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=20,
        )

        response_data = response.json()

        if response.status_code >= 400:
            raise RuntimeError(
                f"WhatsApp API error {response.status_code}: {response_data}"
            )

        return response_data


whatsapp_client = WhatsAppClient()