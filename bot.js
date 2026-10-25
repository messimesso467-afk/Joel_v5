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

// === CONFIGURACIÓN ===
const CONFIG = {
  host: process.env.MC_HOST || '127.0.0.1',
  port: Number(process.env.MC_PORT || 25565), // Puerto estándar de Minecraft
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

// === SISTEMA DE LOGS ===
const LOG_DIR = path.join(__dirname, 'logs')
if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR)
const logFile = path.join(LOG_DIR, `minecraft_${new Date().toISOString().split('T')[0]}.log`)

function log(message) {
  const timestamp = new Date().toISOString()
  const logMessage = `${timestamp} - minecraft_bot - ${message}\n`
  console.log(logMessage.trim())
  fs.appendFileSync(logFile, logMessage)
}

// === NOTIFICACIONES A TELEGRAM ===
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
    if (!respuesta.ok) log(`No pude enviar a Telegram: ${respuesta.status}`)
  } catch (error) {
    log(`Error al enviar a Telegram: ${error.message}`)
  }
}

// === FUNCIONES AUXILIARES ===
function entidadDelJugador() {
  if (miJugador && bot.players[miJugador]?.entity) {
    return bot.players[miJugador].entity
  }
  return bot.nearestEntity(e => e.type === 'player')
}

function prepararMovimiento() {
  bot.pathfinder.setMovements(new Movements(bot))
}

// === RECONEXIÓN AUTOMÁTICA ===
const ESPERA_MAXIMA_CONEXION = 20000
const ESPERA_ENTRE_INTENTOS = 5000

function servidorDisponible() {
  return new Promise(resolver => {
    const socket = net.connect({ host: CONFIG.host, port: CONFIG.port })
    const terminar = resultado => {
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

async function conectar() {
  if (conectando || temporizadorReconexion) return
  conectando = true
  intentosReconexion++
  log(`Intento ${intentosReconexion}: esperando servidor en ${CONFIG.host}:${CONFIG.port}...`)

  if (await servidorDisponible()) {
    await new Promise(r => setTimeout(r, 3000))
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

// === CREAR BOT Y EVENTOS ===
function crearBot() {
  bot = mineflayer.createBot(CONFIG)
  bot.loadPlugin(pathfinder)

  const vigilanteConexion = setTimeout(() => {
    if (bot.entity) return
    log('Sin respuesta — reiniciando conexión...')
    try { bot.quit() } catch {}
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
    log(`✅ Joel conectado a ${CONFIG.host}:${CONFIG.port}`)
    bot.chat('Conectado. A su servicio.')
    await avisarTelegram('Joel se conectó a Minecraft 🎮')
  })

  bot.on('playerJoined', async jugador => {
    log(`Entró: ${jugador.username}`)
    if (miJugador && jugador.username === miJugador) {
      bot.chat('¡Bienvenido! Ya estamos juntos causa.')
      await avisarTelegram(`${miJugador} entró al mundo 🌍`)
    }
  })

  // 🗣️ COMANDOS DIRECTOS DESDE EL CHAT DE MINECRAFT
  bot.on('chat', (quien, texto) => {
    if (quien === bot.username) return
    const t = texto.toLowerCase().normalize('NFD').replace(/[^a-z0-9 ]/g, '')
    log(`[${quien}]: ${t}`)
    if (!miJugador) miJugador = quien

    const tuEntidad = entidadDelJugador()

    if (t.includes('joel sigue') || t.includes('joel sigueme')) {
      if (!tuEntidad) return bot.chat('Acércate más, no te veo pe.')
      prepararMovimiento()
      bot.pathfinder.setGoal(new GoalFollow(tuEntidad, 2), true)
      return bot.chat('¡Voy detrás de ti! 🏃')
    }

    if (t.includes('joel ven')) {
      if (!tuEntidad) return bot.chat('Acércate primero causa.')
      prepararMovimiento()
      bot.pathfinder.setGoal(new GoalNear(tuEntidad.position.x, tuEntidad.position.y, tuEntidad.position.z, 2))
      return bot.chat('¡Ya voy! 🏃')
    }

    if (t.includes('joel para')) {
      bot.pathfinder.stop()
      return bot.chat('Me detengo 🛑')
    }

    if (t.includes('joel salir')) {
      salidaDeliberada = true
      bot.chat('¡Hasta luego bacán! 👋')
      setTimeout(() => bot.quit(), 800)
    }
  })

  bot.on('kicked', async motivo => {
    log(`Expulsado: ${motivo}`)
    await avisarTelegram(`Me expulsaron del servidor ⚠️: ${motivo}`)
  })

  bot.on('error', error => log(`Error: ${error.message}`))

  bot.on('end', async () => {
    clearTimeout(vigilanteConexion)
    log('Desconectado')
    await avisarTelegram('Me desconecté de Minecraft 🔌')
    if (salidaDeliberada) return
    conectar() // Reconecta automáticamente
  })
}

// === SERVIDOR DE ESTADO ===
http.createServer((req, res) => {
  if (req.url !== '/minecraft/status') {
    res.writeHead(404)
    return res.end(JSON.stringify({ error: 'no encontrado' }))
  }
  const conectado = Boolean(bot && bot.entity)
  res.writeHead(200, { 'Content-Type': 'application/json' })
  res.end(JSON.stringify({
    conectado,
    salud: conectado ? bot.health : null,
    jugador: miJugador || null,
    host: CONFIG.host,
    port: CONFIG.port
  }))
}).listen(STATUS_PORT, '0.0.0.0', () => {
  log(`📊 Estado: http://0.0.0.0:${STATUS_PORT}/minecraft/status`)
})

// === SERVIDOR DE CONTROL (para Telegram/Python) ===
if (CONTROL_API_KEY) {
  http.createServer((req, res) => {
    const apiKey = req.headers['x-api-key']
    if (apiKey !== CONTROL_API_KEY) {
      res.writeHead(401)
      return res.end(JSON.stringify({ error: 'API key inválida' }))
    }

    const url = new URL(req.url, `http://${req.headers.host}`)
    const ruta = url.pathname

    // Leer cuerpo
    let cuerpo = ''
    req.on('data', d => cuerpo += d)
    req.on('end', () => {
      const accion = ruta.split('/').pop()

      if (!bot || !bot.entity) {
        res.writeHead(503)
        return res.end(JSON.stringify({ error: 'Bot no conectado' }))
      }

      const tuEntidad = entidadDelJugador()
      if (!tuEntidad && ['ven', 'sigueme'].includes(accion)) {
        res.writeHead(400)
        return res.end(JSON.stringify({ error: 'No hay jugador cerca' }))
      }

      switch (accion) {
        case 'ven':
          prepararMovimiento()
          bot.pathfinder.setGoal(new GoalNear(tuEntidad.position.x, tuEntidad.position.y, tuEntidad.position.z, 2))
          bot.chat('¡Ya voy causa!')
          res.writeHead(200)
          res.end(JSON.stringify({ mensaje: 'Voy hacia ti' }))
          log('Comando: ven')
          break
        case 'sigueme':
          prepararMovimiento()
          bot.pathfinder.setGoal(new GoalFollow(tuEntidad, 2), true)
          bot.chat('Te sigo pe 🏃')
          res.writeHead(200)
          res.end(JSON.stringify({ mensaje: 'Te sigo' }))
          log('Comando: sigueme')
          break
        case 'para':
          bot.pathfinder.stop()
          bot.chat('Me detengo 🛑')
          res.writeHead(200)
          res.end(JSON.stringify({ mensaje: 'Detenido' }))
          log('Comando: para')
          break
        case 'salir':
          salidaDeliberada = true
          bot.chat('Nos vemos causa 👋')
          setTimeout(() => bot.quit(), 800)
          res.writeHead(200)
          res.end(JSON.stringify({ mensaje: 'Desconectando' }))
          log('Comando: salir')
          break
        default:
          res.writeHead(404)
          res.end(JSON.stringify({ error: 'Comando desconocido' }))
      }
    })
  }).listen(CONTROL_PORT, '0.0.0.0', () => {
    log(`🎮 Control activo en puerto ${CONTROL_PORT}`)
  })
} else {
  log('⚠️ MC_CONTROL_API_KEY no configurada — API desactivada')
}

// === ARRANQUE ===
conectar()
