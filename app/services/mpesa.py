import base64
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.config import (
    MPESA_BASE_URL,
    MPESA_CONSUMER_KEY,
    MPESA_CONSUMER_SECRET,
    MPESA_SHORTCODE,
    MPESA_PASSKEY,
)


def get_access_token():
    response = httpx.get(
        f"{MPESA_BASE_URL}/oauth/v1/generate",
        params={"grant_type": "client_credentials"},
        auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def initiate_stk_push(phone, amount, account_reference, callback_url):
    phone = str(phone).replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    if not phone.startswith("254") or len(phone) != 12:
        raise ValueError("Invalid Kenyan phone number")

    if amount <= 0 or float(amount) != int(float(amount)):
        raise ValueError("M-Pesa amount must be a positive whole number")

    timestamp = datetime.now(
        ZoneInfo("Africa/Nairobi")
    ).strftime("%Y%m%d%H%M%S")

    password = base64.b64encode(
        f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()
    ).decode()

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference[:12],
        "TransactionDesc": "FINNEY BITES",
    }

    response = httpx.post(
        f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={"Authorization": f"Bearer {get_access_token()}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
