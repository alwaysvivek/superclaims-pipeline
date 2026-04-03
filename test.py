from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

response = client.post(
    "/api/process",
    data={"claim_id": "test_BYOK", "groq_api_key": "your_groq_api_key_here"},
    files={"file": ("final_image_protected.pdf", open("final_image_protected.pdf", "rb"), "application/pdf")}
)
print("Response Status Code:", response.status_code)
print("Response JSON:")
print(json.dumps(response.json(), indent=2))
