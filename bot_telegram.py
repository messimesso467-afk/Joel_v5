import os
import httpx
import telebot
from dotenv import load_dotenv
import minecraft_client
from joel_core import procesar_respuesta_joel
from logger_config import setup_logger
from config import verificar_dependencias, obtener_config
from memory import memory_manager, CategoriaMemoria

load_dotenv(override=True)
logger = setup_logger("telegram_bot")

if not verificar_dependencias():
    raise RuntimeError("Verifique el archivo .env")

config = obtener_config()
BOT_TOKEN = config["telegram_token"]
CHAT_PERMITIDO = config["telegram_chat_id"]
MC_STATUS_URL = config["mc_status_url"]

bot = telebot.TeleBot(BOT_TOKEN)

def _autorizado(mensaje) -> bool:
    if not CHAT_PERMITIDO:
        return True
    return str(mensaje.chat.id) == str(CHAT_PERMITIDO)

def _orden_mc(mensaje, accion):
    if not _autorizado(mensaje):
        return
    try:
        r = minecraft_client.ejecutar(accion)
        bot.reply_to(mensaje, "✅ " + r["mensaje"])
    except ValueError:
        bot.reply_to(mensaje, "⚠️ Orden no permitida.")
    except Exception:
        bot.reply_to(mensaje, "⚠️ El bot de Minecraft no está encendido (node bot.js).")

@bot.message_handler(commands=["start", "ayuda"])
def bienvenida(m):
    if not _autorizado(m):
        return
    bot.reply_to(m, "Hola, soy Joel 🤖. Escribe /ayuda. Órdenes de Minecraft (sin /): ven, sigueme, para, ponte armadura, come.")

@bot.message_handler(commands=["ven"])
def c_ven(m): _orden_mc(m, "ven")
@bot.message_handler(commands=["sigueme"])
def c_sig(m): _orden_mc(m, "sigueme")
@bot.message_handler(commands=["para"])
def c_para(m): _orden_mc(m, "para")
@bot.message_handler(commands=["salir"])
def c_salir(m): _orden_mc(m, "salir")

@bot.message_handler(func=lambda m: bool(m.text), content_types=["text"])
def recibir_mensaje(mensaje):
    if not _autorizado(mensaje):
        logger.warning(f"Acceso denegado a chat {mensaje.chat.id}")
        return
    if mensaje.text.startswith("/"):
        return

    user_id = f"telegram_{mensaje.from_user.id}"
    logger.info(f"Mensaje de {user_id}: {mensaje.text[:30]}...")

    # 🎮 ÓRDENES DE MINECRAFT POR TEXTO (sin /)
    ordenes = {
        "ven": "ven", "ven a mi": "ven", "ven a mí": "ven", "ven aca": "ven", "ven aquí": "ven",
        "sigueme": "sigueme", "sígueme": "sigueme", "me sigues": "sigueme",
        "para": "para", "detente": "para", "quieto": "para",
        "sal": "salir", "sal del servidor": "salir",
        "ponte armadura": "armadura", "pon la armadura": "armadura", "armadura": "armadura",
        "come": "comer", "come algo": "comer",
    }
    orden_mc = ordenes.get(mensaje.text.lower().strip())
    if orden_mc:
        logger.info(f"Orden Minecraft: {orden_mc}")
        _orden_mc(mensaje, orden_mc)
        return

    # No es orden → responde con la IA (cerebro de Joel)
    respuesta = procesar_respuesta_joel(user_id, mensaje.text)
    bot.reply_to(mensaje, respuesta)

if __name__ == "__main__":
    print("Joel está conectado a Telegram.")
    bot.infinity_polling(skip_pending=True)