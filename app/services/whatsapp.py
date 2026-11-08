import httpx

from app.config import (
    WHATSAPP_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_TEMPLATE_NAME,
    WHATSAPP_API_VERSION,
    WHATSAPP_TEMPLATE_LANGUAGE
)


def whatsapp_is_configured():
    return all([
        WHATSAPP_TOKEN,
        WHATSAPP_PHONE_NUMBER_ID,
        WHATSAPP_TEMPLATE_NAME,
        WHATSAPP_API_VERSION,
        WHATSAPP_TEMPLATE_LANGUAGE
    ])


def whatsapp_status():
    if not whatsapp_is_configured():
        return {
            "configured": False,
            "mode": "dry-run",
            "message": "WhatsApp credentials are incomplete. No message was sent."
        }

    return {
        "configured": True,
        "mode": "live",
        "api_version": WHATSAPP_API_VERSION,
        "message": "WhatsApp configuration is available."
    }


def upload_whatsapp_pdf(pdf_bytes: bytes, filename: str):

    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF document.")

    if not whatsapp_is_configured():
        return {
            "success": False,
            "mode": "dry-run",
            "message": "WhatsApp is not configured. PDF was not uploaded."
        }

    url = (
        f"https://graph.facebook.com/"
        f"{WHATSAPP_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/media"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}"
    }

    files = {
        "file": (filename, pdf_bytes, "application/pdf")
    }

    data = {
        "messaging_product": "whatsapp",
        "type": "application/pdf"
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            files=files,
            data=data,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        media_id = result.get("id")

        if not media_id:
            return {
                "success": False,
                "message": "Meta did not return a media ID."
            }

        return {
            "success": True,
            "media_id": media_id
        }

    except httpx.HTTPError:
        return {
            "success": False,
            "message": "WhatsApp PDF upload failed."
        }


def send_whatsapp_receipt(
    customer_phone: str,
    media_id: str,
    filename: str,
    body_parameters: list[str] | None = None
):

    if not media_id or not filename.lower().endswith(".pdf"):
        raise ValueError("A valid PDF media ID and filename are required.")

    recipient = "".join(
        character for character in customer_phone
        if character.isdigit()
    )

    if recipient.startswith("0"):
        recipient = "254" + recipient[1:]

    if not recipient.startswith("254") or len(recipient) != 12:
        raise ValueError("Invalid Kenyan WhatsApp phone number.")

    if not whatsapp_is_configured():
        return {
            "success": False,
            "mode": "dry-run",
            "message": "WhatsApp is not configured. No message was sent."
        }

    components = [
        {
            "type": "header",
            "parameters": [
                {
                    "type": "document",
                    "document": {
                        "id": media_id,
                        "filename": filename
                    }
                }
            ]
        }
    ]

    if body_parameters:
        components.append({
            "type": "body",
            "parameters": [
                {"type": "text", "text": value}
                for value in body_parameters
            ]
        })

    url = (
        f"https://graph.facebook.com/"
        f"{WHATSAPP_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": {
            "name": WHATSAPP_TEMPLATE_NAME,
            "language": {
                "code": WHATSAPP_TEMPLATE_LANGUAGE
            },
            "components": components
        }
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        return {
            "success": True,
            "message_id": (
                result.get("messages", [{}])[0].get("id")
            )
        }

    except httpx.HTTPError:
        return {
            "success": False,
            "message": "WhatsApp receipt message failed."
        }
