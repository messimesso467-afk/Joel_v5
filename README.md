# JOEL - Asistente Inteligente

JOEL es un asistente de IA integrado con múltiples interfaces: Telegram, Minecraft, API Web y servicios de videoconferencia.

## 📋 Estado Actual

### ✅ Funcionalidades Operativas
- **Cerebro central compartido** (`joel_core.py`): Procesamiento unificado de mensajes
- **Sistema de proveedores de IA**: Arquitectura modular con Gemini y Groq
- **Selección inteligente de modelo**: Según tipo de tarea y disponibilidad
- **Métricas de rendimiento**: Latencia, disponibilidad, tasa de éxito
- **Telegram Bot**: Funcional con comandos y chat
- **Minecraft Bot**: Movimiento básico, reconexión automática, servidor de estado
- **API Web**: FastAPI con endpoint /api/chat
- **Base de datos SQLite**: Historial de conversaciones
- **Sistema de logging**: Logs estructurados en carpeta `logs/`
- **Integración Meet**: Unirse a reuniones Google Meet vía Vexa API
- **Memoria Inteligente**: Sistema avanzado de recuerdos con categorías y búsqueda

### 🔧 Componentes del Proyecto

```
bot-minecraft/
├── joel_core.py           # Cerebro central de JOEL
├── bot_telegram.py        # Bot de Telegram
├── bot.js                 # Bot de Minecraft (Node.js)
├── main.py                # API Web (FastAPI) + panel central
├── auth.py                # Autenticación (X-API-Key y sesión web)
├── rate_limiter.py        # Límite de peticiones por ventana
├── health.py              # Comprobaciones de salud
├── minecraft_client.py    # Cliente Python del control de Minecraft
├── roblox_client.py       # Detección local de Roblox Studio
├── system_manager.py      # Arranque/parada segura de servicios locales
├── iniciar_joel.bat       # Lanzador local de Windows
├── static/                # Centro de control web (HTML/CSS/JS)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── tests/                 # Pruebas automáticas (pytest)
│   └── test_fase4.py
├── database.py            # Gestión de base de datos SQLite
├── config.py              # Configuración centralizada
├── logger_config.py       # Sistema de logging
├── vexa_service.py        # Integración con Google Meet
├── check_dependencies.py  # Script de verificación
├── test_memory.py         # Pruebas de persistencia de memoria
├── test_providers.py      # Pruebas de proveedores de IA
├── test_security.py       # Comprobaciones manuales de seguridad
├── requirements.txt       # Dependencias Python
├── package.json           # Dependencias Node.js
├── .env.example           # Plantilla de configuración
├── .env                   # Configuración real (no versionado)
├── joel_memoria.db        # Base de datos (no versionada)
├── memory/                # Sistema de memoria inteligente
│   ├── __init__.py
│   ├── models.py          # Modelos de datos
│   ├── storage.py         # Operaciones de almacenamiento
│   ├── search.py          # Búsqueda de recuerdos
│   └── manager.py         # Gestor principal
├── providers/             # Sistema de proveedores de IA
│   ├── __init__.py
│   ├── base.py            # Clase base y modelos
│   ├── gemini.py          # Proveedor Google Gemini
│   ├── groq.py            # Proveedor Groq
│   └── manager.py         # Gestor de proveedores
└── logs/                  # Archivos de log
```

## 🚀 Inicio Rápido

### 1. Configuración

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar .env con tus claves API
# - TELEGRAM_BOT_TOKEN (obligatorio)
# - GEMINI_API_KEY o GROQ_API_KEY (obligatorio)
# - API_KEY (obligatorio en Fase 4: protege la API web)
# - MC_CONTROL_API_KEY (obligatorio para controlar Minecraft)
# - VEXA_API_KEY (opcional, para Meet)
# - Configuración de Minecraft (opcional)
```

`API_KEY` y `MC_CONTROL_API_KEY` deben ser cadenas largas y aleatorias.
Puede generarlas con:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Verificar Dependencias

```bash
python check_dependencies.py
```

Este script verifica:
- Variables de entorno configuradas
- Base de datos inicializada
- Configuración válida

### 3. Iniciar Componentes

**Opción recomendada en Windows (lanza todo):**
```
Doble clic en iniciar_joel.bat
```
El lanzador arranca la API web y el bot de Minecraft usando órdenes fijas
(solo escucha en `127.0.0.1`, no se expone a Internet).

**Bot de Telegram:**
```bash
python bot_telegram.py
```

**API Web (solo, manual):**
```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

**Centro de control web:**
Una vez arrancada la API, abra en su navegador:
```
http://127.0.0.1:8000
```
Introduzca su `API_KEY` una sola vez; el servidor guardará una sesión
segura (cookie HttpOnly) y su clave no se almacenará en el navegador.

**Bot de Minecraft:**
```bash
node bot.js
```

## 📊 Características por Componente

### Telegram Bot
- Comandos básicos: `/start`, `/ayuda`, `/estado`
- Órdenes de Minecraft: `/ven`, `/sigueme`, `/para`, `/salir`
- Comandos de memoria: `/memoria`, `/recordar`, `/recuerdos`, `/preferencias`, `/recordatorios`, `/proyectos`, `/borrar`
- Chat conversacional con historial
- Verificación de estado de Minecraft
- Control de acceso por chat_id
- Gestión de recuerdos inteligentes

### Minecraft Bot
- Movimiento: `joel ven`, `joel sigueme`, `joel para`
- Reconexión automática
- Notificaciones a Telegram
- Servidor HTTP de estado (puerto 3847)
- Integración con sistema de logging

### API Web
Todas las rutas privadas exigen la cabecera `X-API-Key` **o** una cookie de
sesión válida. Sin credenciales responden 401; con clave incorrecta, 403; si
no hay `API_KEY` configurada, 503 (fail-closed).

**Rutas públicas**
- `GET /` — centro de control web
- `GET /api/info` — información básica del servidor
- `GET /health` — estado resumido (sin secretos ni rutas internas)
- `GET /api/auth/session` — indica si la sesión del navegador es válida

**Rutas privadas**
- `POST /api/auth/login` — abre sesión con la API key
- `POST /api/auth/logout` — cierra la sesión
- `GET /api/metrics` — métricas de proveedores y salud
- `POST /api/chat` — conversación con el cerebro de JOEL (`user_id`, `message`)
- `GET /api/minecraft/status` — estado real del bot
- `POST /api/minecraft/control` — orden permitida (`ven`, `sigueme`, `para`, `salir`)
- `GET /api/roblox/status` — detección local de Roblox Studio
- `POST /api/roblox/open` — abre Roblox Studio si está instalado
- `GET /api/system/status` — estado de los servicios locales
- `POST /api/system/minecraft/start` / `stop` — arranca/para el bot (orden fija)

Rate limit: 60 peticiones por minuto por identificador.

### Sistema de Memoria
- **Historial de conversaciones**: Últimos 20 mensajes por usuario
- **Memoria inteligente**: Sistema avanzado de recuerdos con categorías
- **Categorías de recuerdos**:
  - `preferencia`: Preferencias del usuario (idioma, tema, etc.)
  - `proyecto`: Información sobre proyectos activos
  - `recordatorio`: Recordatorios pendientes
  - `instruccion`: Instrucciones persistentes
  - `dato`: Datos generales
  - `tarea`: Tareas pendientes
- **Búsqueda**: Por palabras clave, categoría y contexto relevante
- **Persistencia**: Todos los recuerdos se guardan en SQLite
- **Aislamiento**: Los recuerdos están separados por usuario
- **Integración con IA**: JOEL usa recuerdos relevantes para enriquecer sus respuestas

#### Comandos de Memoria en Telegram
- `/recordar <texto>` - Guarda un recuerdo como dato general
- `/recuerdos` - Lista todos tus recuerdos
- `/preferencias` - Lista tus preferencias guardadas
- `/recordatorios` - Lista tus recordatorios pendientes
- `/proyectos` - Lista tus proyectos activos
- `/borrar <id>` - Elimina un recuerdo por su ID

#### Pruebas de Memoria
```bash
python test_memory.py
```
Este script ejecuta pruebas completas de persistencia:
- Guardar y recuperar recuerdos
- Actualizar y eliminar recuerdos
- Búsqueda por palabras clave
- Preferencias y recordatorios
- Persistencia tras "reinicios"

### Sistema de Proveedores de IA
- **Arquitectura modular**: Clase base abstracta para proveedores
- **Proveedores soportados**: Google Gemini, Groq
- **Selección inteligente**: Según tipo de tarea y disponibilidad
- **Reintentos automáticos**: Con exponential backoff
- **Fallback automático**: Si un proveedor falla, prueba con otro
- **Métricas integradas**: Latencia, disponibilidad, tasa de éxito
- **Tipos de tarea**: Chat general, programación, análisis, creativo, razonamiento, resumen

#### Pruebas de Proveedores
```bash
python test_providers.py
```
Este script ejecuta pruebas del sistema de proveedores:
- Inicialización de proveedores
- Selección inteligente
- Generación de respuestas
- Sistema de métricas
- Fallback automático

## 🔒 Seguridad

- Las claves API están en `.env` (no versionado)
- La API web exige `X-API-Key` o sesión con cookie HttpOnly (`SameSite=strict`)
- Las rutas privadas fallan cerradas (503) si falta `API_KEY`
- Rate limiting: 60 peticiones por minuto por identificador
- El control de Minecraft usa una clave separada (`MC_CONTROL_API_KEY`) y
  solo acepta órdenes de una lista blanca
- El navegador nunca recibe ni almacena la API key
- El servidor escucha en `127.0.0.1` (no expuesto a Internet por defecto)
- Sin ejecución arbitraria de comandos: los arranques usan órdenes fijas
- Logs no incluyen secretos (solo prefijos de 6 caracteres en avisos)

## 📝 Logs

Los logs se guardan en `logs/` con formato:
- `joel_YYYYMMDD.log` - Logs de Python
- `minecraft_YYYYMMDD.log` - Logs de Node.js

Niveles de logging:
- INFO: Operaciones normales
- WARNING: Eventos inusuales
- ERROR: Errores que requieren atención
- DEBUG: Información detallada (si se activa)

## 🐛 Troubleshooting

### Error: "Falta TELEGRAM_BOT_TOKEN"
- Asegúrate de configurar la variable en `.env`
- Verifica que el token sea válido

### Error: "Falta GEMINI_API_KEY o GROQ_API_KEY"
- Configura al menos una de las dos en `.env`
- Verifica que la clave sea válida

### Minecraft no se conecta
- Verifica que el servidor esté corriendo
- Revisa la configuración de host y puerto en `.env`
- Consulta los logs en `logs/minecraft_*.log`

### Dependencias faltantes
- Ejecuta `python check_dependencies.py`
- Instala con `pip install -r requirements.txt`
- Para Node.js: `npm install`

## 🎯 Roadmap

### Fase 1: Estabilización ✅
- [x] Backup de base de datos
- [x] Unificar bot de Minecraft
- [x] Sistema de logging estructurado
- [x] Configuración centralizada
- [x] Script de verificación de dependencias

### Fase 2: Memoria Inteligente ✅
- [x] Sistema de categorización de recuerdos
- [x] Búsqueda por palabras clave
- [x] Preferencias por usuario
- [x] Sistema de recordatorios
- [x] Integración con joel_core
- [x] Comandos en Telegram
- [x] Pruebas de persistencia

### Fase 3: Proveedores IA y Selección de Modelos ✅
- [x] Arquitectura modular de proveedores
- [x] Clase base abstracta
- [x] Implementación Gemini
- [x] Implementación Groq
- [x] Gestor unificado de proveedores
- [x] Selección inteligente por tipo de tarea
- [x] Métricas de latencia y disponibilidad
- [x] Reintentos con exponential backoff
- [x] Fallback automático
- [x] Manejo de límites de uso
- [x] Pruebas de proveedores

### Fase 4: Integración Segura ✅
- [x] Autenticación en API Web (X-API-Key + sesión web)
- [x] Rate limiting
- [x] Health checks sistemáticos
- [x] API de control Minecraft separada (puerto 3848, con clave)
- [x] Integración Minecraft con el cerebro de JOEL (`minecraft_client.py`)
- [x] Centro de control web (Inicio, Voz, Minecraft, Roblox Studio, Sistema)
- [x] Detección local de Roblox Studio
- [x] Lanzador local seguro de Windows (`iniciar_joel.bat`)
- [x] Suite de pruebas con pytest (`tests/test_fase4.py`)

### Fase 5: Integración avanzada (Pendiente)
- [ ] Minecraft usa joel_core
- [ ] Comandos inteligentes en Minecraft
- [ ] Respuestas de IA en chat MC

### Fase 6: UX y Web (Pendiente)
- [ ] Automatización de Roblox Studio (Luau, creación de juegos)
- [ ] Interfaz de administración avanzada

## 📄 Licencia

Proyecto personal creado por José Roy.

## 🤝 Contribuciones

Este es un proyecto personal en desarrollo. Las mejoras están documentadas en este README.
