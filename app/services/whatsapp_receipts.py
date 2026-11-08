from app.services.receipts import generate_receipt
from app.services.whatsapp import (
    upload_whatsapp_pdf,
    send_whatsapp_receipt
)


def send_order_receipt_via_whatsapp(order):
    pdf = generate_receipt(order)

    filename = f"{order.order_number}.pdf"

    upload_result = upload_whatsapp_pdf(
        pdf_bytes=pdf,
        filename=filename
    )

    if not upload_result.get("success"):
        return {
            "success": False,
            "stage": "upload",
            "message": upload_result.get(
                "message",
                "Receipt upload failed."
            )
        }

    message_result = send_whatsapp_receipt(
        customer_phone=order.customer_phone,
        media_id=upload_result["media_id"],
        filename=filename
    )

    if not message_result.get("success"):
        return {
            "success": False,
            "stage": "message",
            "message": message_result.get(
                "message",
                "WhatsApp message was not sent."
            )
        }

    return {
        "success": True,
        "order_number": order.order_number,
        "message_id": message_result.get("message_id"),
        "message": "Receipt sent successfully."
    }
