import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "FINNEY BITES")
SECRET_KEY = os.getenv("SECRET_KEY")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./finney_bites.db"
)

BUSINESS_SETTINGS = {
    "name": os.getenv("BUSINESS_NAME", "FINNEY BITES"),
    "tagline": os.getenv(
        "BUSINESS_TAGLINE",
        "Fresh Food, Fast Delivery!"
    ),
    "email": os.getenv(
        "BUSINESS_EMAIL",
        "finneybites@gmail.com"
    ),
    "phone": os.getenv(
        "BUSINESS_PHONE",
        "+254769943592"
    ),
    "whatsapp": os.getenv(
        "WHATSAPP_NUMBER",
        "+254769943592"
    ),
    "mpesa_number": os.getenv(
        "MPESA_NUMBER",
        "+254141941245"
    ),
    "currency": os.getenv("CURRENCY", "KSh"),
    "country": os.getenv("COUNTRY", "Kenya"),
    "location": "Around Zetech University, Kiambu County",
    "timezone": os.getenv("TIMEZONE", "Africa/Nairobi"),
    "opening_hours": {
        "monday": "8:00 AM - 10:00 PM",
        "tuesday": "8:00 AM - 10:00 PM",
        "wednesday": "8:00 AM - 10:00 PM",
        "thursday": "8:00 AM - 10:00 PM",
        "friday": "8:00 AM - 10:00 PM",
        "saturday": "8:00 AM - 10:00 PM",
        "sunday": "Closed"
    },
    "free_delivery_minimum": 2000,
    "delivery_available": True,
    "pickup_available": True
}

# WhatsApp Cloud API configuration
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME")

WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION")

WHATSAPP_TEMPLATE_LANGUAGE = os.getenv(
    "WHATSAPP_TEMPLATE_LANGUAGE",
    "en"
)

# Password reset email settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
SMTP_ENABLED = os.getenv("SMTP_ENABLED", "false").lower() == "true"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:8000")

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_PUBLISHABLE_KEY = os.getenv('SUPABASE_PUBLISHABLE_KEY')

# M-Pesa Daraja Sandbox
MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_ENVIRONMENT = os.getenv("MPESA_ENVIRONMENT", "sandbox")

MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')
