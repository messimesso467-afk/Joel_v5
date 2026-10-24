import os
import re
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from database import init_db, guardar_mensaje, obtener_historial
from vexa_service import entrar_a_reunion

load_dotenv(override=True)
init_db()

MODELO = "llama3.2:1b"
OLLAMA_URL = "http://localhost:11434/api/chat"

app = FastAPI(title="Joel AI - Servidor Principal")

PROMPT_JOEL = """
Te llamas Joel. Eres un asistente limeño alegre, carismático y bromista.
Hablas con jerga peruana ligera (causa, pe, bacán, chévere).
Responde siempre de forma clara, breve, en español y sin emojis.
Si te piden unirte a un Meet o te dan un código (formato abc-defg-hij), indica que estás ingresando.
"""


class ChatRequest(BaseModel):
    user_id: str
    message: str


def procesar_respuesta_joel(user_id: str, mensaje_usuario: str) -> str:
    meet_match = re.search(r'[a-z]{3}-[a-z]{4}-[a-z]{3}', mensaje_usuario.lower())
    prefix_response = ""
    if meet_match:
        code = meet_match.group(0)
        try:
            exito = entrar_a_reunion(code)
        except Exception as e:
            print(f"[Vexa] Error: {e}")
            exito = False
        if exito:
            prefix_response = f"¡Ya me mandé al Meet {code}, causa! Admíteme en la llamada. "
        else:
            prefix_response = f"Intenté entrar al Meet {code} pero hubo un toque de fallo. "

    guardar_mensaje(user_id, "user", mensaje_usuario)
    historial = obtener_historial(user_id)[-20:]

    messages = [{"role": "system", "content": PROMPT_JOEL}] + historial

    try:
        ollama_resp = httpx.post(
            OLLAMA_URL,
            json={
                "model": MODELO,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.7}
            },
            timeout=120
        )
        ollama_resp.raise_for_status()
        data = ollama_resp.json()
        contenido = data.get("message", {}).get("content", "").strip()
    except Exception as e:
        print(f"[Error con Ollama] {e}")
        contenido = f"Se me cruzó un cable con mi cerebro. Error: {str(e)}"

    if not contenido:
        contenido = "Se me quedó pensando, causa. Pregúntamelo otra vez."

    texto_respuesta = prefix_response + contenido
    guardar_mensaje(user_id, "assistant", texto_respuesta)
    return texto_respuesta


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    try:
        reply = procesar_respuesta_joel(req.user_id, req.message)
        return {"response": reply}
    except Exception as e:
        print(f"[Error en /api/chat] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def home():
    return {"status": "Joel AI Web Server Online", "modelo": MODELO}