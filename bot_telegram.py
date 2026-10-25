import os
import httpx
import telebot
from dotenv import load_dotenv
from groq import Groq
import logging

# === CONFIGURACIÓN ===
load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("joel_bot")

# Variables del entorno
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHAT_PERMITIDO = os.getenv("TELEGRAM_CHAT_ID")  # Opcional: tu ID para restringir
MC_BOT_URL = os.getenv("MC_BOT_URL", "http://localhost:3000")  # Donde corre tu bot de Node.js

# Inicializar clientes
bot = telebot.TeleBot(BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# === SISTEMA DE PROMPT DE JOEL ===
PROMPT_SISTEMA = """
Eres Joel, el asistente inspirado en Joel Gonzales de Al fondo hay sitio.
Eres limeño, alegre, bromista, carismático y hablas como gente del pueblo.
Usa jerga peruana natural: causa, pe, bacán, chévere, ya pe, nojoda.
Sin emojis, sin formato raro, máximo 3 o 4 líneas. Habla cercano y amable.
Llama al usuario "causa" o por su nombre si lo sabes. Sé amable y directo.
Si te preguntan por Minecraft, responde como compañero de aventuras.
"""

# === FUNCIONES AUXILIARES ===
def _autorizado(mensaje) -> bool:
    """Verifica si el chat tiene permiso"""
    if not CHAT_PERMITIDO or CHAT_PERMITIDO == "*":
        return True
    return str(mensaje.chat.id) == str(CHAT_PERMITIDO)


def _enviar_a_minecraft(accion: str) -> str:
    """Envía orden al bot de Minecraft (Node.js)"""
    try:
        respuesta = httpx.post(
            f"{MC_BOT_URL}/ejecutar",
            json={"accion": accion},
            timeout=10
        )
        if respuesta.status_code == 200:
            datos = respuesta.json()
            return datos.get("mensaje", "✅ Hecho")
        return f"⚠️ El bot respondió con error: {respuesta.status_code}"
    except httpx.ConnectError:
        return "🔌 No puedo conectarme al bot de Minecraft. Revisa si está encendido (node bot.js)."
    except Exception as e:
        logger.error(f"Error con Minecraft: {e}")
        return "⚠️ Falló la comunicación con Minecraft."


def _preguntar_groq(texto_usuario: str) -> str:
    """Consulta a la IA de Groq"""
    try:
        respuesta = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # ✅ Modelo rápido y potente
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": texto_usuario}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return respuesta.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error con Groq: {e}")
        return "😅 No pude pensar bien, causa. Inténtalo otra vez pe."


# === COMANDOS DE TELEGRAM ===
@bot.message_handler(commands=["start", "ayuda"])
def bienvenida(m):
    if not _autorizado(m):
        return
    bot.reply_to(m,
        "¡Hola causa! 🤖 Soy Joel, tu asistente y compañero de Minecraft.\n\n"
        "Comandos:\n"
        "/ven — Ve a tu posición\n"
        "/sigueme — Te sigue\n"
        "/para — Se detiene\n"
        "/salir — Sale del servidor\n\n"
        "Órdenes sin /:\n"
        "ponte armadura, come, sal del servidor\n\n"
        "O directamente me escribes y charlamos 😄"
    )

@bot.message_handler(commands=["ven"])
def c_ven(m):
    if _autorizado(m):
        bot.reply_to(m, _enviar_a_minecraft("ven"))

@bot.message_handler(commands=["sigueme"])
def c_sig(m):
    if _autorizado(m):
        bot.reply_to(m, _enviar_a_minecraft("sigueme"))

@bot.message_handler(commands=["para"])
def c_para(m):
    if _autorizado(m):
        bot.reply_to(m, _enviar_a_minecraft("para"))

@bot.message_handler(commands=["salir"])
def c_salir(m):
    if _autorizado(m):
        bot.reply_to(m, _enviar_a_minecraft("salir"))


# === MENSAJES DE TEXTO (IA + ÓRDENES LIBRES) ===
@bot.message_handler(func=lambda m: bool(m.text), content_types=["text"])
def procesar_mensaje(mensaje):
    if not _autorizado(mensaje):
        logger.warning(f"Acceso denegado: {mensaje.chat.id}")
        return

    texto = mensaje.text.strip()
    if texto.startswith("/"):
        return  # Ya se maneja arriba

    logger.info(f"Mensaje: {texto[:50]}...")

    # 🎮 Órdenes de Minecraft por texto libre
    ordenes = {
        "ven": "ven", "ven acá": "ven", "ven aquí": "ven", "ven a mí": "ven",
        "sígueme": "sigueme", "sigueme": "sigueme", "ven conmigo": "sigueme",
        "para": "para", "detente": "para", "quieto": "para", "alto": "para",
        "sal": "salir", "salir": "salir", "sal del servidor": "salir",
        "ponte armadura": "armadura", "pon la armadura": "armadura", "armadura": "armadura",
        "come": "comer", "come algo": "comer", "cómete algo": "comer",
    }

    orden = ordenes.get(texto.lower())
    if orden:
        bot.reply_to(mensaje, _enviar_a_minecraft(orden))
        return

    # 🧠 Si no es orden → hablar con la IA de Groq
    respuesta = _preguntar_groq(texto)
    bot.reply_to(mensaje, respuesta)


# === ARRANQUE ===
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ FALTA TELEGRAM_TOKEN en el .env")
        exit(1)
    if not GROQ_API_KEY:
        print("❌ FALTA GROQ_API_KEY en el .env")
        exit(1)

    print("✅ Joel está vivo! 🤖 Conectado a Telegram + Groq + Minecraft")
    bot.infinity_polling(skip_pending=True)
