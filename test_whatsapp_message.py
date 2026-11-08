from app.services.whatsapp import send_whatsapp_receipt

print("TEST 1: Missing WhatsApp credentials")

result = send_whatsapp_receipt(
    customer_phone="0769943592",
    media_id="TEST_MEDIA_ID",
    filename="test_receipt.pdf"
)

print(result)

assert result["success"] is False
assert result["mode"] == "dry-run"

print("\nTEST 2: Invalid phone number")

try:
    send_whatsapp_receipt(
        customer_phone="123",
        media_id="TEST_MEDIA_ID",
        filename="test_receipt.pdf"
    )
    raise AssertionError("Invalid phone number was accepted.")
except ValueError:
    print("PASSED: Invalid phone number rejected.")

print("\nALL TESTS PASSED")
