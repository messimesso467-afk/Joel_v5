require('dotenv').config()

const http = require('http')
const net = require('net')
const mineflayer = require('mineflayer')
const {
  pathfinder,
  Movements,
  goals: { GoalFollow, GoalNear }
} = require('mineflayer-pathfinder')
const fs = require('fs')
const path = require('path')

const CONFIG = {
  host: process.env.MC_HOST || '127.0.0.1',
  port: Number(process.env.MC_PORT || 1024),
  username: process.env.MC_USERNAME || 'Joel',
  version: process.env.MC_VERSION || '1.20.4',
  auth: process.env.MC_AUTH || 'offline'
}

const STATUS_PORT = Number(process.env.MC_STATUS_PORT || 3847)
const CONTROL_PORT = Number(process.env.MC_CONTROL_PORT || 3848)
const CONTROL_API_KEY = process.env.MC_CONTROL_API_KEY || ''
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || ''
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || ''

let bot = null
let miJugador = ''
let temporizadorReconexion = null
let intentosReconexion = 0
let salidaDeliberada = false
let conectando = false

const LOG_DIR = path.join(__dirname, 'logs')
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR)
}

const logFile = path.join(LOG_DIR, `minecraft_${new Date().toISOString().split('T')[0]}.log`)

function log(message) {
  const timestamp = new Date().toISOString()
  const logMessage = `${timestamp} - minecraft_bot - ${message}\n`
  console.log(logMessage.trim())
  fs.appendFileSync(logFile, logMessage)
}

async function avisarTelegram(mensaje) {
  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) return
  try {
    const respuesta = await fetch(
      `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: TELEGRAM_CHAT_ID, text: mensaje })
      }
    )
    if (!respuesta.ok) {
      log(`No pude enviar a Telegram: ${respuesta.status}`)
    }
  } catch (error) {
    log(`No pude enviar a Telegram: ${error.message}`)
  }
}

function entidadDelJugador() {
  if (miJugador && bot.players[miJugador]?.entity) {
    return bot.players[miJugador].entity
  }
  return bot.nearestEntity((entidad) => entidad.type === 'player')
}

function prepararMovimiento() {
  bot.pathfinder.setMovements(new Movements(bot))
}

// Si el servidor aún está cargando, la conexión puede quedarse "a medias":
// no llega ni 'spawn' ni 'end'. Tras este tiempo forzamos el reintento.
const ESPERA_MAXIMA_CONEXION = 20000
const ESPERA_ENTRE_INTENTOS = 5000

// El servidor de Minecraft tarda en arrancar. Si se crea el bot con el puerto
// todavía cerrado, la librería se queda colgada y luego ya no reconecta nunca.
// Por eso comprobamos antes el puerto y solo creamos el bot si responde.
function servidorDisponible() {
  return new Promise((resolver) => {
    const socket = net.connect({ host: CONFIG.host, port: CONFIG.port })
    const terminar = (resultado) => {
      socket.removeAllListeners()
      socket.destroy()
      resolver(resultado)
    }
    socket.setTimeout(3000)
    socket.once('connect', () => terminar(true))
    socket.once('error', () => terminar(false))
    socket.once('timeout', () => terminar(false))
  })
}

// Espera a que el servidor esté disponible y entonces conecta el bot.
async function conectar() {
  if (conectando || temporizadorReconexion) return
  conectando = true
  intentosReconexion += 1
  log(`Intento ${intentosReconexion}: esperando al servidor en ${CONFIG.host}:${CONFIG.port}...`)

  if (await servidorDisponible()) {
    // El puerto ya escucha; damos un margen para que el mundo termine de cargar.
    await new Promise((r) => setTimeout(r, 3000))
    conectando = false
    crearBot()
  } else {
    conectando = false
    temporizadorReconexion = setTimeout(() => {
      temporizadorReconexion = null
      conectar()
    }, ESPERA_ENTRE_INTENTOS)
  }
}

function crearBot() {
  bot = mineflayer.createBot(CONFIG)
  bot.loadPlugin(pathfinder)

  const vigilanteConexion = setTimeout(() => {
    if (bot.entity) return
    log('El servidor no respondió a tiempo. Reinicio la conexión...')
    try {
      bot.quit()
    } catch (error) {
      log(`No pude cerrar la conexión colgada: ${error.message}`)
    }
    conectar()
  }, ESPERA_MAXIMA_CONEXION)

  bot.once('spawn', async () => {
    clearTimeout(vigilanteConexion)
    intentosReconexion = 0
    salidaDeliberada = false
    if (temporizadorReconexion) {
      clearTimeout(temporizadorReconexion)
      temporizadorReconexion = null
    }
    log(`Joel conectado a ${CONFIG.host}:${CONFIG.port}`)
    bot.chat('Conectado. A su servicio.')
    await avisarTelegram('Joel se conectó a Minecraft.')
  })

  bot.on('playerJoined', async (jugador) => {
    log(`Jugador entró: ${jugador.username}`)
    if (miJugador && jugador.username === miJugador) {
      bot.chat('Bienvenido. Ya estamos juntos.')
      await avisarTelegram(`${miJugador} entró al mundo.`)
    }
  })

  bot.on('chat', (quien, texto) => {
    if (quien === bot.username) return

    const t = texto
      .toLowerCase()
      .normalize('NFD')
      .replace(/[^a-z0-9 ]/g, '')
    log(`Dijo ${quien}: ${t}`)
    if (!miJugador) miJugador = quien

    const tuEntidad = entidadDelJugador()

    if (t.includes('joel sigue') || t.includes('joel sigueme')) {
      if (!tuEntidad) return bot.chat('Acérquese más, no lo veo.')
      prepararMovimiento()
      bot.pathfinder.setGoal(new GoalFollow(tuEntidad, 2), true)
      return bot.chat('Le sigo.')
    }

    if (t.includes('joel ven')) {
      if (!tuEntidad) return bot.chat('Acérquese primero.')
      prepararMovimiento()
      bot.pathfinder.setGoal(
        new GoalNear(tuEntidad.position.x, tuEntidad.position.y, tuEntidad.position.z, 2)
      )
      return bot.chat('Voy hacia usted.')
    }

    if (t.includes('joel para')) {
      bot.pathfinder.stop()
      return bot.chat('Me detengo.')
    }

    if (t.includes('joel salir')) {
      salidaDeliberada = true
      bot.chat('Hasta luego.')
      setTimeout(() => bot.quit(), 800)
    }
  })

  bot.on('kicked', async (motivo) => {
    log(`Me expulsaron: ${motivo}`)
    await avisarTelegram('Me expulsaron del mundo.')
  })

  bot.on('error', (error) => {
    log(`Error de Minecraft: ${error.message}`)
  })

  bot.on('end', async () => {
    clearTimeout(vigilanteConexion)
    log('Me desconecté de Minecraft.')
    await avisarTelegram('Me desconecté de Minecraft.')
    if (salidaDeliberada) {
      log('Salida solicitada: no reconecto.')
      return
    }
    conectar()
  })
}

http
  .createServer((req, res) => {
    if (req.url !== '/minecraft/status') {
      res.writeHead(404, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ error: 'no encontrado' }))
      return
    }

    const conectado = Boolean(bot && bot.entity)
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(
      JSON.stringify({
        conectado,
        salud: conectado ? bot.health : null,
        jugador: miJugador || null,
        host: CONFIG.host,
        port: CONFIG.port
      })
    )
  })
  .listen(STATUS_PORT, '127.0.0.1', () => {
    log('Estado Minecraft en http://127.0.0.1:' + STATUS_PORT + '/minecraft/status')
  })

// Servidor de control de Minecraft (API separada)
if (CONTROL_API_KEY) {
  http
    .createServer((req, res) => {
      // Verificar API key
      const apiKey = req.headers['x-api-key']
      if (apiKey !== CONTROL_API_KEY) {
        res.writeHead(401, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ error: 'API key inválida' }))
        return
      }

      // Parsear URL y método
      const url = new URL(req.url, `http://127.0.0.1:${CONTROL_PORT}`)
      const method = req.method
      const path = url.pathname

      // Solo permitir localhost
      if (req.socket.remoteAddress !== '::1' && req.socket.remoteAddress !== '127.0.0.1') {
        res.writeHead(403, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ error: 'Solo conexiones localhost permitidas' }))
        return
      }

      if (path === '/minecraft/control/ven' && method === 'POST') {
        if (!bot || !bot.entity) {
          res.writeHead(503, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ error: 'Bot no conectado' }))
          return
        }

        const tuEntidad = entidadDelJugador()
        if (!tuEntidad) {
          res.writeHead(400, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ error: 'No hay jugador cerca' }))
          return
        }

        prepararMovimiento()
        bot.pathfinder.setGoal(
          new GoalNear(tuEntidad.position.x, tuEntidad.position.y, tuEntidad.position.z, 2)
        )
        bot.chat('Voy hacia usted.')

        res.writeHead(200, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ success: true, action: 'ven' }))
        log('Comando control: ven')
      } else if (path === '/minecraft/control/sigueme' && method === 'POST') {
        if (!bot || !bot.entity) {
          res.writeHead(503, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ error: 'Bot no conectado' }))
          return
        }

        const tuEntidad = entidadDelJugador()
        if (!tuEntidad) {
          res.writeHead(400, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ error: 'No hay jugador cerca' }))
          return
        }

        prepararMovimiento()
        bot.pathfinder.setGoal(new GoalFollow(tuEntidad, 2), true)
        bot.chat('Le sigo.')

        res.writeHead(200, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ success: true, action: 'sigueme' }))
        log('Comando control: sigueme')
      } else if (path === '/minecraft/control/para' && method === 'POST') {
        if (!bot || !bot.entity) {
          res.writeHead(503, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ error: 'Bot no conectado' }))
          return
        }

        bot.pathfinder.stop()
        bot.chat('Me detengo.')

        res.writeHead(200, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ success: true, action: 'para' }))
        log('Comando control: para')
      } else if (path === '/minecraft/control/salir' && method === 'POST') {
        if (!bot || !bot.entity) {
          res.writeHead(503, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ error: 'Bot no conectado' }))
          return
        }

        salidaDeliberada = true
        bot.chat('Hasta luego.')
        setTimeout(() => bot.quit(), 800)

        res.writeHead(200, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ success: true, action: 'salir' }))
        log('Comando control: salir')
      } else {
        res.writeHead(404, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ error: 'Endpoint no encontrado' }))
      }
    })
    .listen(CONTROL_PORT, '127.0.0.1', () => {
      log('Control Minecraft en http://127.0.0.1:' + CONTROL_PORT)
    })
} else {
  log('Control API no iniciado: falta MC_CONTROL_API_KEY en .env')
}

conectar()
