# JOEL en la nube — Comparación, elección y plan

**Fecha:** 22 de octubre de 2026
**Presupuesto objetivo:** S/0 (0 pesos)
**Estado:** análisis y preparación. **Nada desplegado, nada publicado.**

> **Decisión del 22/10/2026:** al no contar con tarjeta, la nube elegida es
> **Wispbyte** (€0, sin tarjeta, no duerme) para el núcleo Python, y
> **Minecraft queda en la PC con túnel**. La ruta Oracle de este documento
> queda como alternativa para el futuro, si consigue tarjeta de verificación.

---

## 1. Qué es JOEL hoy (análisis del proyecto real)

Revisé el código en su PC. Esto es lo que hay:

**Servicios Python** (`requirements.txt`): FastAPI 0.110, uvicorn 0.28, python-dotenv,
requests, pydantic, httpx, pyTelegramBotAPI, groq.

**Servicios Node** (`package.json`): mineflayer 4.39 + mineflayer-pathfinder.

**Datos**: una sola base SQLite, `joel_memoria.db` (52 KB hoy), más la carpeta `logs/`.

| Componente | Archivo | ¿Debe estar encendido? | Peso |
|---|---|---|---|
| Panel web + API | [main.py](file:///c:/Users/DIANA/bot-minecraft/main.py) | **Siempre** (para abrirlo desde la TV/PC/celular) | ~90 MB RAM |
| Cerebro IA (Groq / Gemini) | `providers/` | Bajo demanda (solo al chatear) | ~0 |
| Memoria | `database.py`, `memory/` | Siempre (acompaña a la web) | ~0 |
| Bot de Telegram | [bot_telegram.py](file:///c:/Users/DIANA/bot-minecraft/bot_telegram.py) | **Siempre** (usa *polling*: si se apaga, no responde) | ~80 MB RAM |
| Bot de Minecraft | [bot.js](file:///c:/Users/DIANA/bot-minecraft/bot.js) | Solo si juega | ~150 MB RAM |
| Servidor de Minecraft (Paper 1.20.4) | `servidor_minecraft/` | Solo si juega | **~1 GB RAM + Java** |
| Roblox Studio | [roblox_client.py](file:///c:/Users/DIANA/bot-minecraft/roblox_client.py) | Solo si usa Roblox | Windows |

### Los tres hechos que deciden todo

1. **La memoria es un archivo SQLite.** Si el disco de la nube es efímero, los recuerdos de JOEL
   se borran en cada reinicio. Necesitamos **disco persistente**.
2. **El bot de Telegram usa polling.** Es un proceso que debe vivir 24/7. En un servicio que
   "duerme" por inactividad, JOEL deja de contestar por Telegram.
3. **El servidor de Minecraft pesa ~1 GB de RAM y abre puertos de juego.** Ningún servicio
   gratuito "sin servidor" puede con eso.

### Una ventaja: JOEL ya está bien aislado

`main.py` no arranca el servidor de Minecraft ni el bot desde la web (solo *consulta* su estado
vía HTTP), y toda la configuración sale de `.env`. Eso significa que **el núcleo Python se puede
mover a la nube sin tocar las Fases 1–3**.

---

## 2. Comparación de nubes (verificado en documentación oficial, oct. 2026)

| Nube | Plan gratuito real | ¿Duerme? | Disco persistente | RAM | Tarjeta | Sirve para JOEL |
|---|---|---|---|---|---|---|
| **Oracle Cloud** (Always Free) | **Sí, permanente**: 2 OCPU ARM + **12 GB RAM** + 200 GB disco; 2 VM AMD micro | **No** | **Sí** (block storage) | **12 GB** | Sí, solo verificación | **Sí, todo el núcleo — y hasta Minecraft** |
| **Google Cloud Run** (Always Free) | Sí, permanente: 2 M peticiones, 180.000 vCPU-s, 360.000 GiB-s/mes | Sí (escala a cero) | **No** | configurable | Sí | Parcial: necesita reescribir Telegram a *webhook* y sacar la BD de SQLite |
| **Google Cloud** (VM e2-micro) | Sí, permanente: 1 vCPU + **1 GB RAM** + 30 GB, solo 3 regiones de EE. UU. | No | Sí | **1 GB** | Sí | Web + Telegram sí; Minecraft no |
| **Render** (Free) | Sí, permanente: 512 MB / 0,1 CPU, 750 h/mes | **Sí, a los 15 min** | **No (efímero)** | 512 MB | No | **No**: pierde la memoria y Telegram se cae al dormir |
| **Koyeb** (Free) | Sí: 1 servicio, 512 MB, **0,1 vCPU**, 2 GB disco | Sí (escala a cero) | Limitado | 512 MB | Según región | **No**: 0,1 vCPU y se duerme |
| **Fly.io** | **Eliminado** (oct. 2024). Solo prueba | — | — | — | Sí | No |
| **Railway** | **No hay plan gratis**: $5 de prueba (30 días), luego desde $5/mes | — | — | — | Sí | No (coste > S/0) |
| **Hugging Face Spaces** | Docker/Gradio ahora **exigen plan de pago**; gratis = 2 Spaces ZeroGPU | Sí (48 h) | No por defecto | 16 GB | — | No |

**Conclusión de la comparación:** solo **Oracle Cloud Always Free** ofrece, gratis y para siempre,
un servidor **encendido 24/7 con disco persistente**, que es exactamente lo que JOEL necesita.
Es además el único que puede alojar el servidor de Minecraft sin gastar nada.

> Render y Koyeb tienen planes gratuitos reales, pero su diseño (dormir + disco efímero) choca
> con dos requisitos de JOEL: memoria permanente y Telegram siempre activo.

---

## 3. Elección recomendada: **Oracle Cloud Always Free**

**Qué pide y qué da**

- 1 instancia ARM `VM.Standard.A1.Flex`: **2 OCPU + 12 GB RAM** (1.500 OCPU-hora y 9.000 GB-hora
  al mes). Antes eran 4 OCPU/24 GB; **desde junio de 2026 son 2 OCPU/12 GB**. Sigue siendo de
  sobra para JOEL.
- **200 GB** de almacenamiento en bloque → disco persistente para `joel_memoria.db`.
- Tráfico de salida gratuito muy amplio (10 TB/mes).
- **Coste real de mantener JOEL: S/0.** El núcleo consume ~300 MB de los 12 GB.

**Por qué gana**

1. Es el único S/0 **sin dormir**: Telegram y el panel siguen vivos.
2. **Disco persistente**: la memoria de JOEL no se borra.
3. **12 GB de RAM**: cabe el núcleo y, si algún día quiere, también Minecraft.
4. **No hay que tocar las Fases 1–3**: el código funciona tal cual, solo cambian variables de `.env`.

**Riesgos reales (no los escondo)**

| Riesgo | Detalle | Mitigación |
|---|---|---|
| Piden **tarjeta** | Solo para verificar identidad. No se cobra si no sube de plan | No active "Pay As You Go" |
| **Recuperan instancias inactivas** | Regla oficial: si en 7 días el CPU, la red y la memoria están por debajo del 20 % (percentil 95), pueden reclamarla | JOEL hace trabajo real (Telegram + health checks); además puede añadir una tarea ligera de mantenimiento |
| **Falta de cupo ARM** | En algunas regiones/zona no hay ARM libre al crear la VM | Probar otra zona de disponibilidad o esperar |
| **Mantenimiento** | Usted es el administrador (actualizaciones, copias) | Copia diaria de la BD por `cron` (ya incluida en la guía) |
| **TV antigua** | El navegador del Smart TV debe aceptar HTTPS y cookies | Probar en la TV antes de dar por cerrado |

---

## 4. Arquitectura por módulos (así JOEL funciona gratis desde el día 1)

```
        ┌──────────────────── NUBE (Oracle, siempre encendida, S/0) ───────────────────┐
        │  Panel web HTTPS  +  Cerebro IA (Groq/Gemini)  +  Memoria SQLite  +  Telegram │
        │                    2 OCPU ARM · 12 GB RAM · 200 GB disco                      │
        └───────────────┬──────────────────────────────────────────────────────────────┘
                        │  (opcional, túnel cifrado saliente)
        ┌───────────────▼───────────────┐      ┌───────────────────────────────────────┐
        │  SU PC (solo si la enciende)   │      │  Módulo C · Roblox Studio (Windows)   │
        │  Paper 1.20.4 + bot.js (:3847) │      │  Solo funciona con la PC encendida    │
        └────────────────────────────────┘      └───────────────────────────────────────┘
```

- **Módulo A — Núcleo (nube):** panel, chat, memoria y Telegram. **Funciona sin su PC.**
- **Módulo B — Minecraft:** al principio en su PC; se puede subir a la VM cuando quiera.
- **Módulo C — Roblox:** se queda en Windows por limitación del sistema, no por elección.

---

## 5. Qué funcionará de verdad (y qué no)

**Funciona sin encender la PC:** el panel en la TV/PC/celular, el chat con IA, la memoria
(recordar y consultar), y el bot de Telegram.

**Necesita la PC encendida:**
- **Roblox Studio**: es Windows. Desde la nube el panel solo dirá "no disponible".
- **Minecraft**, *si lo deja en la PC* (Módulo B2). Si pasa a la opción B1 (en la VM), también
  funcionará con la PC apagada.

**Cómo se abre JOEL:** siempre con una URL `https://...` en el navegador. En el PC y el celular
es directo. En un Smart TV JVC depende de que su navegador soporte HTTPS y cookies modernas;
si no, queda la opción de una app/barra lateral o de usar el celular para controlar.

---

## 6. Plan de despliegue (para ejecutar **solo tras su aprobación**)

1. **Copiar/duplicar el `.env`**: se generan claves nuevas y **fuertes** para la nube.
   *(Ahora mismo `API_KEY` es `joel2026`, y quedó visible en esta sesión junto con el token de
   Telegram y la clave de Groq: hay que **rotar los tres**.)*
2. **Repositorio privado en GitHub** con el `.gitignore` reforzado (el `.env` nunca entra).
3. **Crear la VM Oracle** (2 OCPU / 12 GB / Ubuntu ARM) y abrir solo 22, 80 y 443.
4. **Desplegar con Docker Compose** (archivos ya preparados en `deploy/`).
5. **HTTPS con Caddy** + nombre `nip.io` o dominio propio.
6. **Restaurar su memoria actual** subiendo una copia de `joel_memoria.db`.
7. **Pruebas reales**: `/health`, login, chat, memoria y Telegram. Se le entrega la evidencia.
8. **Copia de seguridad diaria** de la BD por `cron`.
9. (Opcional, después) Módulo B1: Minecraft dentro de la VM.

### Archivos ya preparados (creados, **sin usar**)

- [Dockerfile](file:///c:/Users/DIANA/bot-minecraft/deploy/Dockerfile) — imagen del núcleo Python.
- [docker-compose.yml](file:///c:/Users/DIANA/bot-minecraft/deploy/docker-compose.yml) — panel + Telegram.
- [env.cloud.example](file:///c:/Users/DIANA/bot-minecraft/deploy/env.cloud.example) — plantilla sin claves.
- [Caddyfile](file:///c:/Users/DIANA/bot-minecraft/deploy/Caddyfile) — HTTPS automático.
- [README-DESPLIEGUE.md](file:///c:/Users/DIANA/bot-minecraft/deploy/README-DESPLIEGUE.md) — pasos detallados.
- [.dockerignore](file:///c:/Users/DIANA/bot-minecraft/.dockerignore) — evita que `.env` y la BD entren en la imagen.

### Dos cambios mínimos de código que necesitaré proponerle

No los he aplicado: **esperan su aprobación**.

1. **Cookie segura en HTTPS**: en [main.py](file:///c:/Users/DIANA/bot-minecraft/main.py#L152-L167) la
   cookie de sesión no lleva `secure=True`. En la nube conviene activarlo.
2. **Control de Minecraft por túnel** (solo si elige B2): en
   [minecraft_client.py](file:///c:/Users/DIANA/bot-minecraft/minecraft_client.py#L45-L46) la URL de
   control está fija en `127.0.0.1`; habría que leerla también de `.env`.

---

## 7. Costes

| Concepto | Coste |
|---|---|
| VM Oracle Always Free (2 OCPU / 12 GB / 200 GB) | **S/0** |
| HTTPS (Caddy + Let's Encrypt) | **S/0** |
| Nombre `nip.io` | **S/0** |
| Dominio propio (opcional) | ~US$10/año (**no necesario**) |
| IA (Groq / Gemini, planes gratuitos) | **S/0** |
| Telegram Bot API | **S/0** |
| **Total** | **S/0** |

---

## 8. Lo que necesito de usted para continuar

1. ¿Aprueba **Oracle Cloud Always Free** como destino, o prefiere que evalúe su alternativa?
2. ¿Tiene **tarjeta** para la verificación de identidad de Oracle? (No se cobra.)
3. ¿Crea usted el **repositorio privado de GitHub**, o prefiere que le dé los comandos exactos?
4. ¿Minecraft en la **nube (B1)** o en su **PC con túnel (B2)**?

Con sus respuestas ejecuto los pasos 1–8 y le entrego la **evidencia real** (salud, login,
chat, memoria y URL funcionando).

---

### Fuentes

- [Render — Deploy for Free (spin-down, sistema de archivos efímero)](https://render.com/docs/free)
- [Render — ¿Es gratis? El sueño de 15 minutos y la base de 30 días](https://justinmckelvey.com/blog/is-render-free)
- [Render Free Tier explicado](https://unanswered.io/guide/render-free-tier-details)
- [Koyeb — plan gratuito 2026 (512 MB, 0,1 vCPU, escala a cero)](https://stacksfree.com/blog/koyeb-free-tier-2026/)
- [Koyeb vs capa gratuita de contenedores](https://snapdeploy.dev/blog/koyeb-vs-free-container-tier)
- [Google Cloud — características gratuitas (Cloud Run y VM e2-micro)](https://cloudwebschool.com/docs/gcp/fundamentals/free-tier/)
- [GCP Free Tier 2026 (límites de Cloud Run)](https://agentdeals.dev/gcp-free-tier-2026)
- [Oracle — Always Free Resources (1.500 OCPU-h y 9.000 GB-h; equivale a 2 OCPU y 12 GB)](https://oracle.hydrogen.sagittarius.connect.product.adaptavist.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
- [Oracle — reglas de recuperación de instancias inactivas](https://oracommit.blogspot.com/2026/02/understanding-oci-always-free-compute.html)
- [Oracle ARM Always Free en 2026: límites reales](https://autokaam.com/tutorials/oracle-arm-always-free-tier-2026-real-limits/)
- [Fly.io — sin capa gratuita para organizaciones nuevas](https://hostingsift.com/hosting/fly-io)
- [Railway — precios y prueba de 5 USD](https://docs.railway.com/reference/pricing/free-trial)
- [Hugging Face Spaces — la capa gratuita 2026](https://stacksfree.com/blog/hugging-face-spaces-free-tier-guide-2026/)
- [Cloudflare Tunnel — documentación oficial](https://developers.cloudflare.com/tunnel/get-started/)
