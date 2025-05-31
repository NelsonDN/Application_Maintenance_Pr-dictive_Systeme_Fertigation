/**
 * Script principal pour l'application de maintenance prédictive
 */

// Initialisation au chargement du document
document.addEventListener("DOMContentLoaded", () => {
  // Initialiser les éléments d'interface
  initUI()

  // Initialiser la connexion WebSocket
  initWebSocket()

  // Mettre à jour la date et l'heure
  updateDateTime()
  setInterval(updateDateTime, 1000)
})

/**
 * Initialise les éléments d'interface
 */
function initUI() {
  // Toggle du sidebar
  const sidebarToggle = document.getElementById("sidebar-toggle")
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      document.querySelector(".sidebar").classList.toggle("show")
    })
  }

  // Fermer les messages flash automatiquement
  const flashMessages = document.querySelectorAll(".alert-dismissible")
  flashMessages.forEach((alert) => {
    setTimeout(() => {
      const closeButton = alert.querySelector(".btn-close")
      if (closeButton) {
        closeButton.click()
      }
    }, 5000)
  })
}

/**
 * Initialise la connexion WebSocket
 */
function initWebSocket() {
  // Vérifier si Socket.IO est disponible
  if (typeof io === "undefined") {
    console.error("Socket.IO n'est pas chargé")
    return
  }

  // Connexion au serveur Socket.IO
  const socket = io()

  // Événement de connexion
  socket.on("connect", () => {
    console.log("WebSocket connecté")
    updateMQTTStatus({ connected: true, message: "Connexion établie" })
  })

  // Événement de déconnexion
  socket.on("disconnect", () => {
    console.log("WebSocket déconnecté")
    updateMQTTStatus({ connected: false, message: "Connexion perdue" })
  })

  // Événement de statut MQTT
  socket.on("mqtt_status", (data) => {
    updateMQTTStatus(data)
  })

  // Événement de nouvelle alerte
  socket.on("new_alert", (data) => {
    handleNewAlert(data)
  })

  // Événement de données de capteur
  socket.on("sensor_data", (data) => {
    updateSensorData(data)
  })

  // Événement de statut système
  socket.on("system_status", (data) => {
    updateSystemStatus(data)
  })

  // Stocker la connexion socket pour une utilisation ultérieure
  window.appSocket = socket
}

/**
 * Met à jour le statut MQTT dans l'interface
 */
function updateMQTTStatus(data) {
  const statusIcon = document.getElementById("mqtt-status-icon")
  const statusText = document.getElementById("mqtt-status-text")

  if (!statusIcon || !statusText) return

  if (data.connected) {
    statusIcon.className = "status-icon"
    statusText.textContent = data.message || "Connecté"
  } else {
    statusIcon.className = "status-icon disconnected"
    statusText.textContent = data.message || "Déconnecté"
  }
}

/**
 * Gère une nouvelle alerte
 */
function handleNewAlert(alert) {
  // Mettre à jour le compteur d'alertes
  const alertsBadge = document.getElementById("alerts-badge")
  if (alertsBadge) {
    alertsBadge.classList.remove("d-none")
    const currentCount = Number.parseInt(alertsBadge.textContent) || 0
    alertsBadge.textContent = currentCount + 1
  }

  // Afficher une notification si disponible
  if ("Notification" in window && Notification.permission === "granted") {
    const notification = new Notification("Nouvelle alerte", {
      body: `${alert.sensor_name}: ${alert.message}`,
      icon: "/static/images/logo.png",
    })
  }

  // Jouer un son d'alerte si disponible
  const alertSound = document.getElementById("alert-sound")
  if (alertSound) {
    alertSound.play().catch((e) => console.log("Impossible de jouer le son d'alerte"))
  }
}

/**
 * Met à jour les données de capteur dans l'interface
 */
function updateSensorData(data) {
  // Mettre à jour la valeur du capteur si l'élément existe
  const valueElement = document.getElementById(`${data.sensor_name}-value`)
  if (valueElement) {
    valueElement.textContent = `${data.value} ${data.unit}`
  }

  // Mettre à jour le statut du capteur
  const statusElement = document.getElementById(`${data.sensor_name}-status`)
  if (statusElement) {
    if (data.anomalies_count > 0) {
      statusElement.innerHTML = '<i class="fas fa-circle text-danger"></i>'
    } else {
      statusElement.innerHTML = '<i class="fas fa-circle text-success"></i>'
    }
  }

  // Émettre un événement personnalisé pour les graphiques
  const event = new CustomEvent("sensor-data-update", { detail: data })
  document.dispatchEvent(event)
}

/**
 * Met à jour le statut du système
 */
function updateSystemStatus(data) {
  const systemStatus = document.getElementById("system-status")
  if (systemStatus) {
    if (data.errors && data.errors.length > 0) {
      systemStatus.textContent = `Système en alerte (${data.errors.length} erreurs)`
      systemStatus.className = "text-warning"
    } else {
      systemStatus.textContent = `Système en ligne (${formatUptime(data.uptime)})`
      systemStatus.className = "text-success"
    }
  }
}

/**
 * Formate le temps de fonctionnement
 */
function formatUptime(seconds) {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  let result = ""
  if (days > 0) result += `${days}j `
  if (hours > 0 || days > 0) result += `${hours}h `
  result += `${minutes}m`

  return result
}

/**
 * Met à jour la date et l'heure actuelles
 */
function updateDateTime() {
  const dateTimeElement = document.getElementById("current-datetime")
  if (dateTimeElement) {
    const now = new Date()
    const options = {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }
    dateTimeElement.textContent = now.toLocaleDateString("fr-FR", options)
  }
}

/**
 * Formate une date pour l'affichage
 */
function formatDate(dateString) {
  if (!dateString) return "--"

  const date = new Date(dateString)
  const options = {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }

  return date.toLocaleDateString("fr-FR", options)
}

/**
 * Exporte des données au format CSV
 */
function exportToCSV(data, filename) {
  // Créer les en-têtes CSV
  const headers = Object.keys(data[0]).join(",")

  // Créer les lignes de données
  const rows = data
    .map((item) => {
      return Object.values(item)
        .map((value) => {
          // Échapper les virgules et les guillemets
          if (typeof value === "string") {
            value = value.replace(/"/g, '""')
            if (value.includes(",") || value.includes('"') || value.includes("\n")) {
              value = `"${value}"`
            }
          }
          return value
        })
        .join(",")
    })
    .join("\n")

  // Combiner les en-têtes et les lignes
  const csv = `${headers}\n${rows}`

  // Créer un blob et un lien de téléchargement
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.setAttribute("href", url)
  link.setAttribute("download", filename)
  link.style.visibility = "hidden"
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
