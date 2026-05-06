import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.config import settings
from app.whatsapp_client import whatsapp_client
from app.chatbot_service import get_chatbot_answer


router = APIRouter(
    prefix="/whatsapp",
    tags=["WhatsApp"],
)


JUSTCORP_WEBSITE_URL = os.getenv(
    "JUSTCORP_WEBSITE_URL",
    "https://justcorplabs.netlify.app",
)


class WhatsAppSendTestRequest(BaseModel):
    to: str
    message: str


@router.get("/webhook")
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    """
    WhatsApp webhook verification endpoint.
    """

    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        if hub_challenge and hub_challenge.isdigit():
            return int(hub_challenge)

        return hub_challenge

    raise HTTPException(
        status_code=403,
        detail="WhatsApp webhook verification failed.",
    )


def extract_whatsapp_messages(payload: Dict[str, Any]) -> List[Dict[str, Optional[str]]]:
    """
    Extract text messages from a WhatsApp Cloud API webhook payload.

    This safely ignores delivery receipts and status-only webhook events.
    """

    extracted_messages: List[Dict[str, Optional[str]]] = []

    entries = payload.get("entry", [])

    for entry in entries:
        changes = entry.get("changes", [])

        for change in changes:
            value = change.get("value", {})

            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            contact_name = None

            if contacts:
                contact_profile = contacts[0].get("profile", {})
                contact_name = contact_profile.get("name")

            for message in messages:
                message_type = message.get("type")
                sender_phone = message.get("from")
                message_id = message.get("id")
                timestamp = message.get("timestamp")

                text_body = None

                if message_type == "text":
                    text_data = message.get("text", {})
                    text_body = text_data.get("body")

                extracted_messages.append(
                    {
                        "message_id": message_id,
                        "sender_phone": sender_phone,
                        "sender_name": contact_name,
                        "message_type": message_type,
                        "text": text_body,
                        "timestamp": timestamp,
                    }
                )

    return extracted_messages


def should_include_website_link(user_text: str) -> bool:
    """
    Decide whether to include a website link in the WhatsApp reply.

    The website link is useful when users ask about:
    - services
    - contact details
    - website
    - pricing
    - booking
    - demos
    - business help
    """

    if not user_text:
        return False

    text = user_text.lower()

    website_keywords = [
        "website",
        "site",
        "link",
        "contact",
        "services",
        "offer",
        "pricing",
        "price",
        "cost",
        "demo",
        "book",
        "consultation",
        "business",
        "justcorp",
        "justcorp labs",
        "more information",
    ]

    return any(keyword in text for keyword in website_keywords)


def format_whatsapp_answer(
    sender_name: str,
    answer: str,
    sources: List[Dict[str, Any]],
    include_website_link: bool = False,
) -> str:
    """
    Format the RAG answer for WhatsApp.

    This keeps the answer clean and adds a website call-to-action when useful.
    """

    greeting = f"Hi {sender_name}, this is JustCorp Labs AI Assistant."

    message_parts = [
        greeting,
        answer,
    ]

    if sources:
        source_lines = []

        for source in sources[:3]:
            filename = source.get("filename", "Uploaded document")
            chunk_number = source.get("chunk_number", "N/A")
            source_lines.append(f"- {filename} | Chunk {chunk_number}")

        sources_text = "\n".join(source_lines)

        message_parts.append(
            f"Sources used:\n{sources_text}"
        )

    if include_website_link:
        message_parts.append(
            f"To learn more or contact us, visit:\n{JUSTCORP_WEBSITE_URL}"
        )

    return "\n\n".join(message_parts)


@router.post("/webhook")
async def receive_whatsapp_webhook(payload: dict):
    """
    Receive incoming WhatsApp messages and reply using the RAG chatbot.

    Flow:
    - Meta sends incoming WhatsApp message event to this endpoint
    - We extract the sender phone number and text message
    - We pass the text into the RAG knowledge base
    - We send the generated answer back to WhatsApp
    """

    print("Incoming WhatsApp webhook payload:", payload)

    parsed_messages = extract_whatsapp_messages(payload)

    if not parsed_messages:
        return {
            "status": "received",
            "message": "Webhook received, but no text messages were found. This may be a status update.",
            "parsed_messages": [],
        }

    replies_sent = []

    for msg in parsed_messages:
        sender_phone = msg.get("sender_phone")
        sender_name = msg.get("sender_name") or "there"
        message_type = msg.get("message_type")
        user_text = msg.get("text")

        if not sender_phone:
            replies_sent.append(
                {
                    "to": None,
                    "status": "skipped",
                    "reason": "No sender phone number found.",
                }
            )
            continue

        if message_type != "text" or not user_text:
            reply_text = (
                "Hi, this is JustCorp Labs AI Assistant.\n\n"
                "Please send a text question so I can search the knowledge base for you.\n\n"
                f"You can also visit our website here:\n{JUSTCORP_WEBSITE_URL}"
            )
        else:
            chatbot_result = get_chatbot_answer(
                question=user_text,
                top_k=4,
            )

            answer = chatbot_result.get(
                "answer",
                "Sorry, I could not generate an answer right now.",
            )

            sources = chatbot_result.get("sources", [])

            reply_text = format_whatsapp_answer(
                sender_name=sender_name,
                answer=answer,
                sources=sources,
                include_website_link=should_include_website_link(user_text),
            )

        try:
            result = whatsapp_client.send_text_message(
                to_phone_number=sender_phone,
                message_text=reply_text,
            )

            print("WhatsApp RAG reply sent:", result)

            replies_sent.append(
                {
                    "to": sender_phone,
                    "status": "sent",
                    "meta_response": result,
                }
            )

        except Exception as error:
            print("WhatsApp RAG reply failed:", str(error))

            replies_sent.append(
                {
                    "to": sender_phone,
                    "status": "failed",
                    "error": str(error),
                }
            )

    return {
        "status": "received",
        "message": "WhatsApp message payload parsed and RAG replies attempted.",
        "parsed_messages": parsed_messages,
        "replies_sent": replies_sent,
    }


@router.post("/send-test")
def send_test_whatsapp_message(request: WhatsAppSendTestRequest):
    """
    Send a test WhatsApp message using Meta WhatsApp Cloud API.
    """

    try:
        result = whatsapp_client.send_text_message(
            to_phone_number=request.to,
            message_text=request.message,
        )

        return {
            "status": "sent",
            "message": "WhatsApp test message sent successfully.",
            "to": request.to,
            "meta_response": result,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )