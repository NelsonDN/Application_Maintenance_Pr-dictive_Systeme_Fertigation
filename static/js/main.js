/**
 * Script principal pour la gestion WebSocket et fonctionnalités communes
 */

// Variables globales
let socket = null
let isConnected = false
let reconnectAttempts = 0
const maxReconnectAttempts = 5
const io = window.io // Declare the io variable
const bootstrap = window.bootstrap // Declare the bootstrap variable

// Initialisation au chargement de la page
document.addEventListener("DOMContentLoaded", () => {
  initializeWebSocket()
  initializeCommonFeatures()
  updateDateTime()
  setInterval(updateDateTime, 1000)
})

/**
 * Initialise la connexion WebSocket
 */
function initializeWebSocket() {
  try {
    socket = io()

    socket.on("connect", () => {
      console.log("✅ WebSocket connecté")
      isConnected = true
      reconnectAttempts = 0
      updateConnectionStatus(true)
    })

    socket.on("disconnect", () => {
      console.log("❌ WebSocket déconnecté")
      isConnected = false
      updateConnectionStatus(false)
    })

    socket.on("connect_error", (error) => {
      console.error("❌ Erreur de connexion WebSocket:", error)
      handleReconnection()
    })

    // Écouter les données de capteurs en temps réel
    socket.on("sensor_data", (data) => {
      updateSensorValue(data)
    })

    // Écouter les nouvelles alertes
    socket.on("new_alert", (alert) => {
      handleNewAlert(alert)
    })

    // Écouter les alertes résolues
    socket.on("alert_resolved", (data) => {
      handleAlertResolved(data)
    })

    // Écouter les mises à jour du statut système
    socket.on("system_status", (status) => {
      updateSystemStatus(status)
    })
  } catch (error) {
    console.error("❌ Erreur lors de l'initialisation WebSocket:", error)
  }
}

/**
 * Gère la reconnexion automatique
 */
function handleReconnection() {
  if (reconnectAttempts < maxReconnectAttempts) {
    reconnectAttempts++
    console.log(`🔄 Tentative de reconnexion ${reconnectAttempts}/${maxReconnectAttempts}`)
    setTimeout(() => {
      socket.connect()
    }, 2000 * reconnectAttempts)
  } else {
    console.error("❌ Impossible de se reconnecter après plusieurs tentatives")
    updateConnectionStatus(false, "Connexion perdue")
  }
}

/**
 * Met à jour le statut de connexion dans l'interface
 */
function updateConnectionStatus(connected, message = null) {
  const statusElement = document.getElementById("connection-status")
  const httpStatusIcon = document.getElementById("http-status-icon")
  const httpStatusText = document.getElementById("http-status-text")

  if (statusElement) {
    const icon = statusElement.querySelector("i")
    const text = statusElement.querySelector("span")

    if (connected) {
      icon.className = "fas fa-circle text-success"
      text.textContent = "Temps réel actif  "
    } else {
      icon.className = "fas fa-circle text-danger"
      text.textContent = message || "Connexion perdue"
    }
  }

  if (httpStatusIcon && httpStatusText) {
    if (connected) {
      httpStatusIcon.textContent = "🟢"
      httpStatusText.textContent = "Communication active"
    } else {
      httpStatusIcon.textContent = "🔴"
      httpStatusText.textContent = "Communication interrompue"
    }
  }
}

/**
 * Met à jour la valeur d'un capteur en temps réel
 */
function updateSensorValue(data) {
  const sensorName = data.sensor_name
  const value = data.value
  const unit = data.unit
  const timestamp = new Date(data.timestamp)

  // Mettre à jour la valeur affichée
  const valueElement = document.getElementById(`${sensorName}-value`)
  if (valueElement) {
    valueElement.textContent = `${value} ${unit}`

    // Animation de mise à jour
    valueElement.classList.add("updated")
    setTimeout(() => {
      valueElement.classList.remove("updated")
    }, 1000)
  }

  // Mettre à jour le statut du capteur
  const statusElement = document.getElementById(`${sensorName}-status`)
  if (statusElement) {
    const icon = statusElement.querySelector("i")
    if (data.anomalies_count > 0) {
      icon.className = "fas fa-circle text-warning"
    } else {
      icon.className = "fas fa-circle text-success"
    }
  }

  // Mettre à jour l'heure de dernière mise à jour
  const lastUpdateElement = document.getElementById("last-update-time")
  if (lastUpdateElement) {
    lastUpdateElement.textContent = `Dernière mise à jour: ${timestamp.toLocaleTimeString()}`
  }

  // Émettre un événement personnalisé pour les graphiques
  document.dispatchEvent(
    new CustomEvent("sensorDataUpdate", {
      detail: data,
    }),
  )
}

/**
 * Gère l'affichage d'une nouvelle alerte
 */
function handleNewAlert(alert) {
  console.log("🚨 Nouvelle alerte:", alert)

  // Mettre à jour le badge d'alertes
  updateAlertsCount()

  // Afficher une notification
  showNotification("Nouvelle alerte", alert.message, "warning")

  // Ajouter l'alerte à la liste si on est sur la page des alertes
  if (window.location.pathname.includes("/alerts")) {
    addAlertToList(alert) // Declare the addAlertToList function
  }

  // Mettre à jour la liste des alertes récentes sur le dashboard
  if (window.location.pathname === "/" || window.location.pathname.includes("/dashboard")) {
    updateRecentAlertsList() // Declare the updateRecentAlertsList function
  }
}

/**
 * Gère la résolution d'une alerte
 */
function handleAlertResolved(data) {
  console.log("✅ Alerte résolue:", data)

  // Mettre à jour le badge d'alertes
  updateAlertsCount()

  // Supprimer l'alerte de la liste
  const alertElement = document.querySelector(`[data-alert-id="${data.alert_id}"]`)
  if (alertElement) {
    alertElement.remove()
  }

  // Afficher une notification
  showNotification("Alerte résolue", "Une alerte a été résolue avec succès", "success")
}

/**
 * Met à jour le compteur d'alertes
 */
function updateAlertsCount() {
  fetch("/api/alerts_count")
    .then((response) => response.json())
    .then((data) => {
      const badge = document.getElementById("alerts-badge")
      const countElement = document.getElementById("active-alerts-count")

      if (badge) {
        if (data.active_count > 0) {
          badge.textContent = data.active_count
          badge.classList.remove("d-none")
        } else {
          badge.classList.add("d-none")
        }
      }

      if (countElement) {
        countElement.textContent = data.active_count
      }
    })
    .catch((error) => {
      console.error("❌ Erreur lors de la récupération du nombre d'alertes:", error)
    })
}

/**
 * Affiche une notification toast
 */
function showNotification(title, message, type = "info") {
  // Créer l'élément de notification
  const notification = document.createElement("div")
  notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`
  notification.innerHTML = `
        <strong>${title}</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `

  // Ajouter au container de notifications
  let container = document.getElementById("notification-container")
  if (!container) {
    container = document.createElement("div")
    container.id = "notification-container"
    container.className = "notification-container"
    document.body.appendChild(container)
  }

  container.appendChild(notification)

  // Supprimer automatiquement après 5 secondes
  setTimeout(() => {
    if (notification.parentNode) {
      notification.remove()
    }
  }, 5000)
}

/**
 * Met à jour la date et l'heure
 */
function updateDateTime() {
  const now = new Date()
  const dateTimeElement = document.getElementById("current-datetime")
  if (dateTimeElement) {
    dateTimeElement.textContent = now.toLocaleString("fr-FR")
  }
}

/**
 * Initialise les fonctionnalités communes
 */
function initializeCommonFeatures() {
  // Toggle sidebar
  const sidebarToggle = document.getElementById("sidebar-toggle")
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      document.body.classList.toggle("sidebar-collapsed")
    })
  }

  // Initialiser les tooltips Bootstrap
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))

  // Mettre à jour le compteur d'alertes au chargement
  updateAlertsCount()
}

/**
 * Met à jour le statut du système
 */
function updateSystemStatus(status) {
  const systemStatusElement = document.getElementById("system-status")
  if (systemStatusElement) {
    systemStatusElement.textContent = `Système actif - ${status.uptime || 0}s`
  }
}

/**
 * Utilitaire pour formater les nombres
 */
function formatNumber(value, decimals = 1) {
  return Number.parseFloat(value).toFixed(decimals)
}

/**
 * Utilitaire pour formater les dates
 */
function formatDateTime(dateString) {
  const date = new Date(dateString)
  return date.toLocaleString("fr-FR")
}

/**
 * Exporte les fonctions pour utilisation dans d'autres scripts
 */
window.MainApp = {
  socket,
  isConnected: () => isConnected,
  updateSensorValue,
  showNotification,
  formatNumber,
  formatDateTime,
}

// Declare the addAlertToList function
function addAlertToList(alert) {
  // Implementation for adding alert to list
  console.log("Adding alert to list:", alert)
}

// Declare the updateRecentAlertsList function
function updateRecentAlertsList() {
  // Implementation for updating recent alerts list
  console.log("Updating recent alerts list")
}
