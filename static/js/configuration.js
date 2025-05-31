/**
 * Script pour la page Configuration avec HTTP
 */

document.addEventListener("DOMContentLoaded", () => {
  initializeConfiguration()
  setupEventListeners()
  updateSystemStatus()
  startLogUpdates()
})

/**
 * Initialise la configuration
 */
function initializeConfiguration() {
  console.log("⚙️ Initialisation de la configuration HTTP")

  // Vérifier le statut WebSocket
  updateWebSocketStatus()

  // Charger les logs récents
  loadRecentLogs()
}

/**
 * Configure les écouteurs d'événements
 */
function setupEventListeners() {
  // Test de l'endpoint HTTP
  const testHttpBtn = document.getElementById("test-http-btn")
  if (testHttpBtn) {
    testHttpBtn.addEventListener("click", testHttpEndpoint)
  }

  // Redémarrage du simulateur
  const restartSimulatorBtn = document.getElementById("restart-simulator-btn")
  if (restartSimulatorBtn) {
    restartSimulatorBtn.addEventListener("click", restartSimulator)
  }

  // Sauvegarde des seuils
  const saveThresholdsBtn = document.getElementById("save-thresholds-btn")
  if (saveThresholdsBtn) {
    saveThresholdsBtn.addEventListener("click", saveThresholds)
  }

  // Sauvegarde des paramètres Weibull
  const saveWeibullBtn = document.getElementById("save-weibull-btn")
  if (saveWeibullBtn) {
    saveWeibullBtn.addEventListener("click", saveWeibullParameters)
  }

  // Sauvegarde de la base de données
  const backupDbBtn = document.getElementById("backup-db-btn")
  if (backupDbBtn) {
    backupDbBtn.addEventListener("click", backupDatabase)
  }

  // Nettoyage des anciennes données
  const clearOldDataBtn = document.getElementById("clear-old-data-btn")
  if (clearOldDataBtn) {
    clearOldDataBtn.addEventListener("click", clearOldData)
  }

  // Réinitialisation du système
  const resetSystemBtn = document.getElementById("reset-system-btn")
  if (resetSystemBtn) {
    resetSystemBtn.addEventListener("click", resetSystem)
  }

  // Vider les logs
  const clearLogsBtn = document.getElementById("clear-logs-btn")
  if (clearLogsBtn) {
    clearLogsBtn.addEventListener("click", clearLogs)
  }

  // Actualiser les logs
  const refreshLogsBtn = document.getElementById("refresh-logs-btn")
  if (refreshLogsBtn) {
    refreshLogsBtn.addEventListener("click", loadRecentLogs)
  }
}

/**
 * Test de l'endpoint HTTP
 */
function testHttpEndpoint() {
  const button = document.getElementById("test-http-btn")
  const originalText = button.innerHTML

  button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Test en cours...'
  button.disabled = true

  // Données de test
  const testData = {
    sensor_type: "test",
    test_value: 123.45,
    timestamp: new Date().toISOString(),
  }

  fetch("/api/sensor_data", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(testData),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        showNotification("Test réussi", "L'endpoint HTTP fonctionne correctement", "success")
        updateHttpStatus(true)
      } else {
        showNotification("Test échoué", data.error || "Erreur inconnue", "danger")
      }
    })
    .catch((error) => {
      console.error("❌ Erreur test HTTP:", error)
      showNotification("Test échoué", "Impossible de contacter l'endpoint", "danger")
      updateHttpStatus(false)
    })
    .finally(() => {
      button.innerHTML = originalText
      button.disabled = false
    })
}

/**
 * Redémarre le simulateur
 */
function restartSimulator() {
  const button = document.getElementById("restart-simulator-btn")
  const originalText = button.innerHTML

  button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Redémarrage...'
  button.disabled = true

  // Simuler le redémarrage (dans une vraie application, cela ferait un appel API)
  setTimeout(() => {
    showNotification("Simulateur redémarré", "Le simulateur HTTP a été redémarré avec succès", "success")
    addLogEntry("INFO: Simulateur HTTP redémarré")
    button.innerHTML = originalText
    button.disabled = false
  }, 2000)
}

/**
 * Sauvegarde les seuils
 */
function saveThresholds() {
  const thresholds = {}
  const inputs = document.querySelectorAll(".threshold-input")

  inputs.forEach((input) => {
    const sensor = input.dataset.sensor
    const type = input.dataset.type
    const value = Number.parseFloat(input.value)

    if (!thresholds[sensor]) {
      thresholds[sensor] = {}
    }
    thresholds[sensor][type] = value
  })

  console.log("💾 Sauvegarde des seuils:", thresholds)
  showNotification("Seuils sauvegardés", "Les seuils des capteurs ont été mis à jour", "success")
  addLogEntry("INFO: Seuils des capteurs mis à jour")
}

/**
 * Sauvegarde les paramètres Weibull
 */
function saveWeibullParameters() {
  const parameters = {}
  const inputs = document.querySelectorAll(".weibull-input")

  inputs.forEach((input) => {
    const sensor = input.dataset.sensor
    const param = input.dataset.param
    const value = Number.parseFloat(input.value)

    if (!parameters[sensor]) {
      parameters[sensor] = {}
    }
    parameters[sensor][param] = value
  })

  console.log("💾 Sauvegarde des paramètres Weibull:", parameters)
  showNotification("Paramètres sauvegardés", "Les paramètres de Weibull ont été mis à jour", "success")
  addLogEntry("INFO: Paramètres Weibull mis à jour")
}

/**
 * Sauvegarde la base de données
 */
function backupDatabase() {
  const button = document.getElementById("backup-db-btn")
  const originalText = button.innerHTML

  button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sauvegarde...'
  button.disabled = true

  // Simuler la sauvegarde
  setTimeout(() => {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-")
    const filename = `backup_${timestamp}.db`

    showNotification("Sauvegarde créée", `Base de données sauvegardée: ${filename}`, "success")
    addLogEntry(`INFO: Sauvegarde créée: ${filename}`)

    button.innerHTML = originalText
    button.disabled = false
  }, 3000)
}

/**
 * Nettoie les anciennes données
 */
function clearOldData() {
  if (confirm("Êtes-vous sûr de vouloir supprimer les anciennes données ?")) {
    const button = document.getElementById("clear-old-data-btn")
    const originalText = button.innerHTML

    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Nettoyage...'
    button.disabled = true

    setTimeout(() => {
      showNotification("Nettoyage terminé", "Les anciennes données ont été supprimées", "success")
      addLogEntry("INFO: Anciennes données supprimées")

      button.innerHTML = originalText
      button.disabled = false
    }, 2000)
  }
}

/**
 * Réinitialise le système
 */
function resetSystem() {
  if (confirm("Êtes-vous sûr de vouloir réinitialiser le système ? Cette action est irréversible.")) {
    const button = document.getElementById("reset-system-btn")
    const originalText = button.innerHTML

    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Réinitialisation...'
    button.disabled = true

    setTimeout(() => {
      showNotification("Système réinitialisé", "Le système a été réinitialisé avec succès", "warning")
      addLogEntry("WARNING: Système réinitialisé")

      button.innerHTML = originalText
      button.disabled = false
    }, 3000)
  }
}

/**
 * Met à jour le statut WebSocket
 */
function updateWebSocketStatus() {
  const statusText = document.getElementById("websocket-status-text")
  const statusBadge = document.getElementById("websocket-status-badge")

  if (window.MainApp && window.MainApp.isConnected()) {
    if (statusText) statusText.textContent = "Connexion WebSocket active"
    if (statusBadge) {
      statusBadge.textContent = "CONNECTÉ"
      statusBadge.className = "badge bg-success"
    }
  } else {
    if (statusText) statusText.textContent = "Connexion WebSocket fermée"
    if (statusBadge) {
      statusBadge.textContent = "DÉCONNECTÉ"
      statusBadge.className = "badge bg-danger"
    }
  }
}

/**
 * Met à jour le statut HTTP
 */
function updateHttpStatus(connected) {
  const statusText = document.getElementById("http-status-text")
  const statusIcon = document.getElementById("http-status-icon")

  if (connected) {
    if (statusText) statusText.textContent = "Serveur actif - /api/sensor_data"
    if (statusIcon) statusIcon.className = "fas fa-globe text-success"
  } else {
    if (statusText) statusText.textContent = "Serveur inactif"
    if (statusIcon) statusIcon.className = "fas fa-globe text-danger"
  }
}

/**
 * Met à jour le statut du système
 */
function updateSystemStatus() {
  // Vérifier périodiquement le statut WebSocket
  setInterval(updateWebSocketStatus, 5000)
}

/**
 * Charge les logs récents
 */
function loadRecentLogs() {
  // Dans une vraie application, cela ferait un appel API
  // Ici on simule avec des logs statiques
  addLogEntry("INFO: Logs actualisés")
}

/**
 * Démarre les mises à jour des logs
 */
function startLogUpdates() {
  // Écouter les événements WebSocket pour les logs temps réel
  if (window.MainApp && window.MainApp.socket) {
    window.MainApp.socket.on("system_log", (logData) => {
      addLogEntry(`${logData.level}: ${logData.message}`)
    })
  }
}

/**
 * Ajoute une entrée de log
 */
function addLogEntry(message) {
  const logsContainer = document.getElementById("system-logs")
  if (logsContainer) {
    const timestamp = new Date().toLocaleString("fr-FR")
    const logLine = `[${timestamp}] ${message}\n`

    logsContainer.textContent += logLine

    // Faire défiler vers le bas
    logsContainer.scrollTop = logsContainer.scrollHeight

    // Limiter le nombre de lignes
    const lines = logsContainer.textContent.split("\n")
    if (lines.length > 100) {
      logsContainer.textContent = lines.slice(-100).join("\n")
    }
  }
}

/**
 * Vide les logs
 */
function clearLogs() {
  const logsContainer = document.getElementById("system-logs")
  if (logsContainer) {
    logsContainer.textContent = `[${new Date().toLocaleString("fr-FR")}] INFO: Logs vidés\n`
  }
}

/**
 * Affiche une notification
 */
function showNotification(title, message, type = "info") {
  if (window.MainApp && window.MainApp.showNotification) {
    window.MainApp.showNotification(title, message, type)
  } else {
    alert(`${title}: ${message}`)
  }
}

// Exporter pour utilisation globale
window.ConfigurationApp = {
  testHttpEndpoint,
  updateWebSocketStatus,
  addLogEntry,
}
