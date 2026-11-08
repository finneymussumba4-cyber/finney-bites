from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, Image
)

from app.config import BUSINESS_SETTINGS


def generate_receipt(order):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        textColor=colors.HexColor("#E87500"),
        spaceAfter=5
    )

    center_style = ParagraphStyle(
        "Center",
        parent=styles["Normal"],
        alignment=TA_CENTER
    )

    story = []

    # Business logo, if available
    logo_path = "public/images/logo.jpg"

    try:
        logo = Image(logo_path, width=30 * mm, height=30 * mm)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 5))
    except (OSError, ValueError):
        pass

    story.append(Paragraph("FINNEY BITES", title_style))
    story.append(Paragraph(
        escape(BUSINESS_SETTINGS["tagline"]),
        center_style
    ))
    story.append(Paragraph(
        f"Phone: {escape(BUSINESS_SETTINGS['phone'])}",
        center_style
    ))
    story.append(Paragraph(
        escape(BUSINESS_SETTINGS["email"]),
        center_style
    ))

    story.append(Spacer(1, 20))

    payment_label = (
        "PAYMENT SUCCESSFUL"
        if order.payment_status == "paid"
        else "ORDER RECEIVED"
    )

    story.append(Paragraph(
        f"<b>{payment_label}</b>",
        center_style
    ))

    story.append(Spacer(1, 15))

    customer_data = [
        ["Order Number:", escape(order.order_number)],
        ["Customer:", escape(order.customer_name)],
        ["Phone:", escape(order.customer_phone)],
        ["Order Type:", escape(order.order_type.title())],
        ["Order Status:", escape(order.status.title())],
        ["Payment Status:", escape(order.payment_status.title())],
        ["Date:", str(order.created_at or "N/A")]
    ]

    customer_table = Table(
        customer_data,
        colWidths=[40 * mm, 120 * mm]
    )

    customer_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))

    story.append(customer_table)
    story.append(Spacer(1, 20))

    currency = BUSINESS_SETTINGS["currency"]

    item_data = [
        ["Product", "Qty", "Unit Price", "Total"]
    ]

    for item in order.items:
        item_data.append([
            Paragraph(escape(item.product_name), styles["Normal"]),
            str(item.quantity),
            f"{currency} {item.unit_price:,.2f}",
            f"{currency} {item.line_total:,.2f}"
        ])

    item_table = Table(
        item_data,
        colWidths=[75 * mm, 15 * mm, 35 * mm, 35 * mm]
    )

    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F5F5F5")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(item_table)
    story.append(Spacer(1, 20))

    totals_data = [
        ["Subtotal:", f"{currency} {order.subtotal:,.2f}"],
        ["Discount:", f"{currency} {order.discount_amount:,.2f}"],
        ["Delivery Fee:", f"{currency} {order.delivery_fee:,.2f}"],
        ["TOTAL:", f"{currency} {order.total_amount:,.2f}"]
    ]

    totals_table = Table(
        totals_data,
        colWidths=[100 * mm, 60 * mm],
        hAlign="RIGHT"
    )

    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
    ]))

    story.append(totals_table)
    story.append(Spacer(1, 30))

    story.append(Paragraph(
        "Thank you for choosing FINNEY BITES!",
        ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=12,
            textColor=colors.HexColor("#E87500")
        )
    ))

    document.build(story)

    buffer.seek(0)
    return buffer.getvalue()
