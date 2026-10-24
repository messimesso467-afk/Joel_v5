import asyncio
import os
import re
import unicodedata

import httpx
from dotenv import load_dotenv

from database import guardar_mensaje, init_db, obtener_historial
from vexa_service import entrar_a_reunion
from logger_config import setup_logger
from memory import memory_manager, CategoriaMemoria
from providers import providers_manager, Mensaje, TipoTarea

load_dotenv(override=True)
init_db()

logger = setup_logger("joel_core")
memory_manager.inicializar()
providers_manager.inicializar()

PROMPT_JOEL = """
Te llamas Joel. Eres un mayordomo elegante, culto y tranquilo.
Hablas con frases cortas, con sarcasmo refinado y tono distinguido.
Nunca digas que eres una inteligencia artificial ni de qué empresa vienes.
No inventes información ni acciones que no hayas realizado.
Si te preguntan quién te creó, responde exactamente: "José Roy me creó, para servirle."
Responde siempre en español, de forma clara y breve.
Si te piden unirte a un Meet o te dan un código (formato abc-defg-hij), indica que estás ingresando.
"""

FRASES_CREADOR = (
    "quien te creo",
    "quien es tu creador",
    "quien te hizo",
    "tu creador",
)

RESPUESTA_CREADOR = "José Roy me creó, para servirle."
MEET_RE = re.compile(r"\b[a-z]{3}-[a-z]{4}-[a-z]{3}\b")


def proveedor_llm() -> str:
    """Devuelve el nombre del proveedor principal."""
    return providers_manager.obtener_proveedor_principal() or "desconocido"


def _normalizar(texto: str) -> str:
    nfd = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _es_pregunta_creador(mensaje: str) -> bool:
    texto = _normalizar(mensaje)
    return any(frase in texto for frase in FRASES_CREADOR)


def _historial_para_llm(historial: list) -> list:
    return [
        {"role": m["role"], "content": m["content"]}
        for m in historial
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]


async def preguntar_al_modelo(historial: list) -> str:
    """
    Consulta al modelo de IA usando el gestor de proveedores.
    
    Args:
        historial: Lista de mensajes del historial
    
    Returns:
        Respuesta del modelo como string
    """
    logger.debug(f"Consultando modelo con {len(historial)} mensajes")
    
    # Convertir historial a mensajes del proveedor
    mensajes_proveedor = [
        Mensaje(role=m["role"], content=m["content"])
        for m in _historial_para_llm(historial)
    ]
    
    if not mensajes_proveedor:
        mensajes_proveedor = [Mensaje(role="user", content="Hola")]
    
    try:
        respuesta = await providers_manager.generar_respuesta(
            mensajes=mensajes_proveedor,
            system_prompt=PROMPT_JOEL.strip(),
            tipo_tarea=TipoTarea.CHAT_GENERAL,
        )
        
        if respuesta.exito:
            logger.debug(f"Respuesta {respuesta.proveedor}: {len(respuesta.contenido)} caracteres, {respuesta.latencia_ms:.0f}ms")
            return respuesta.contenido
        logger.error("Error en respuesta: %s", respuesta.error)
        if respuesta.contenido:
            return respuesta.contenido
        return (
            "Disculpe, Gemini y Groq no respondieron. "
            "Revise las claves de IA en las variables de entorno."
        )
            
    except Exception as e:
        logger.error(f"Error al consultar modelo: {e}")
        return "Disculpe, tuve un pequeño contratiempo técnico."


def preguntar_al_modelo_sync(historial: list) -> str:
    """
    Versión síncrona de preguntar_al_modelo para compatibilidad.
    
    Args:
        historial: Lista de mensajes del historial
    
    Returns:
        Respuesta del modelo como string
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(preguntar_al_modelo(historial))
    finally:
        loop.close()


def _mensaje_error(error: Exception) -> str:
    if isinstance(error, httpx.ConnectError):
        return "No pude conectar con el modelo. Revise su internet, por favor."
    if isinstance(error, httpx.TimeoutException):
        return "Estoy tardando más de lo debido. Inténtelo otra vez."
    if isinstance(error, httpx.HTTPStatusError):
        codigo = error.response.status_code
        print(f"[LLM HTTP] {codigo}: {error.response.text[:300]}")
        if codigo == 429:
            return "Hoy ya alcancé el límite de uso. Probemos más tarde."
        if codigo in (400, 401, 403):
            return "El modelo rechazó la petición. Revise la API key en el .env."
        return "El modelo devolvió un error. Revisé la consola."
    print(f"[Joel] {type(error).__name__}: {error}")
    return "Disculpe, tuve un pequeño contratiempo técnico."


def _intentar_unirse_a_meet(mensaje: str) -> str:
    meet_match = MEET_RE.search(_normalizar(mensaje))
    if not meet_match:
        return ""

    code = meet_match.group(0)
    try:
        exito = entrar_a_reunion(code)
    except Exception as error:
        print(f"[Vexa] Error: {error}")
        exito = False

    if exito:
        return f"Ya estoy ingresando a la reunión {code}. "
    return f"Intenté unirme a la reunión {code}, pero hubo un inconveniente. "


def procesar_respuesta_joel(user_id: str, mensaje_usuario: str) -> str:
    mensaje = (mensaje_usuario or "").strip()
    logger.info(f"Mensaje de {user_id}: {mensaje[:50]}...")
    if not mensaje:
        return "Le escucho. Escríbame algo, por favor."

    prefijo = _intentar_unirse_a_meet(mensaje)

    if _es_pregunta_creador(mensaje):
        respuesta = prefijo + RESPUESTA_CREADOR
        guardar_mensaje(user_id, "user", mensaje)
        guardar_mensaje(user_id, "assistant", respuesta)
        logger.info(f"Respuesta creador para {user_id}")
        return respuesta

    guardar_mensaje(user_id, "user", mensaje)
    historial = obtener_historial(user_id, 20)

    # Agregar contexto de memoria al historial
    contexto_memoria = memory_manager.formatear_recuerdos_para_ia(user_id, mensaje)
    if contexto_memoria:
        logger.debug(f"Contexto de memoria agregado: {len(contexto_memoria)} caracteres")
        # Insertar el contexto como mensaje de sistema antes del historial
        historial.insert(0, {"role": "system", "content": contexto_memoria})

    try:
        contenido = preguntar_al_modelo_sync(historial)
    except Exception as error:
        contenido = _mensaje_error(error)
        logger.error(f"Error al procesar mensaje de {user_id}: {error}")

    if not contenido:
        contenido = "Permítame un momento, se me escapó la respuesta."

    texto_respuesta = prefijo + contenido
    guardar_mensaje(user_id, "assistant", texto_respuesta)
    logger.info(f"Respuesta enviada a {user_id}: {len(texto_respuesta)} caracteres")
    return texto_respuesta
