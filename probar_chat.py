import httpx

url = "http://127.0.0.1:8080/api/chat"
payload = {
    "user_id": "jose_roy",
    "message": "¿Quién te creó?"
}

try:
    respuesta = httpx.post(url, json=payload, timeout=10)
    print("Respuesta de Joel:", respuesta.json())
except Exception as e:
    print("Error al conectar:", e)