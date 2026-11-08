from app.services.whatsapp import upload_whatsapp_pdf

print("TEST 1: Invalid PDF")

try:
    upload_whatsapp_pdf(b"NOT A PDF", "test.pdf")
    raise AssertionError("Invalid PDF was accepted.")
except ValueError:
    print("PASSED: Invalid PDF rejected.")

print("\nTEST 2: Missing WhatsApp credentials")

result = upload_whatsapp_pdf(b"%PDF-1.4 test", "test.pdf")
print(result)

assert result["success"] is False
assert result["mode"] == "dry-run"

print("\nALL TESTS PASSED")
