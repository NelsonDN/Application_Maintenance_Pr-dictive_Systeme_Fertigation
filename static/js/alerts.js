/**
 * Script pour la page des alertes
 */

document.addEventListener("DOMContentLoaded", () => {
  initializeAlerts()
  setupEventListeners()
})

/**
 * Initialise la page des alertes
 */
function initializeAlerts() {
  console.log("🚨 Initialisation de la page des alertes")
}

/**
 * Configure les écouteurs d'événements
 */
function setupEventListeners() {
  // Boutons de résolution d'alertes
  const resolveButtons = document.querySelectorAll(".resolve-alert-btn")
  resolveButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const alertId = this.getAttribute("data-alert-id")
      resolveAlert(alertId)
    })
  })

  // Bouton d'actualisation
  const refreshButton = document.getElementById("refresh-alerts")
  if (refreshButton) {
    refreshButton.addEventListener("click", () => {
      location.reload()
    })
  }

  // Écouter les nouvelles alertes via WebSocket
  if (window.MainApp && window.MainApp.socket) {
    window.MainApp.socket.on("new_alert", (alert) => {
      addNewAlertToTable(alert)
    })

    window.MainApp.socket.on("alert_resolved", (data) => {
      removeAlertFromTable(data.alert_id)
    })
  }
}

/**
 * Résout une alerte
 */
function resolveAlert(alertId) {
  const button = document.querySelector(`[data-alert-id="${alertId}"]`)
  const originalText = button.innerHTML

  // Désactiver le bouton et afficher le chargement
  button.disabled = true
  button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Résolution...'

  fetch(`/alerts/resolve/${alertId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Supprimer la ligne du tableau
        removeAlertFromTable(alertId)

        // Afficher une notification de succès
        if (window.MainApp && window.MainApp.showNotification) {
          window.MainApp.showNotification("Alerte résolue", "L'alerte a été résolue avec succès", "success")
        }
      } else {
        throw new Error(data.error || "Erreur lors de la résolution")
      }
    })
    .catch((error) => {
      console.error("❌ Erreur lors de la résolution de l'alerte:", error)

      // Restaurer le bouton
      button.disabled = false
      button.innerHTML = originalText

      // Afficher une notification d'erreur
      if (window.MainApp && window.MainApp.showNotification) {
        window.MainApp.showNotification("Erreur", "Impossible de résoudre l'alerte", "danger")
      } else {
        alert("Erreur lors de la résolution de l'alerte")
      }
    })
}

/**
 * Ajoute une nouvelle alerte au tableau
 */
function addNewAlertToTable(alert) {
  const tableBody = document.getElementById("active-alerts-table")
  if (!tableBody) return

  // Supprimer le message "Aucune alerte" s'il existe
  const noAlertsMessage = document.querySelector(".no-alerts-message")
  if (noAlertsMessage) {
    noAlertsMessage.remove()
  }

  const row = document.createElement("tr")
  row.setAttribute("data-alert-id", alert.id)
  row.innerHTML = `
        <td><span class="sensor-badge">${alert.sensor_name}</span></td>
        <td>${alert.type}</td>
        <td>${alert.message}</td>
        <td><span class="badge bg-${getSeverityClass(alert.severity)}">${alert.severity.toUpperCase()}</span></td>
        <td>${new Date(alert.timestamp).toLocaleString("fr-FR")}</td>
        <td>
            <button class="btn btn-sm btn-success resolve-alert-btn" data-alert-id="${alert.id}">
                <i class="fas fa-check me-1"></i>Résoudre
            </button>
        </td>
    `

  // Ajouter l'écouteur d'événement au nouveau bouton
  const resolveButton = row.querySelector(".resolve-alert-btn")
  resolveButton.addEventListener("click", function () {
    const alertId = this.getAttribute("data-alert-id")
    resolveAlert(alertId)
  })

  // Ajouter en haut du tableau
  tableBody.insertBefore(row, tableBody.firstChild)
}

/**
 * Supprime une alerte du tableau
 */
function removeAlertFromTable(alertId) {
  const row = document.querySelector(`tr[data-alert-id="${alertId}"]`)
  if (row) {
    row.remove()

    // Vérifier s'il reste des alertes
    const tableBody = document.getElementById("active-alerts-table")
    if (tableBody && tableBody.children.length === 0) {
      const noAlertsMessage = document.createElement("div")
      noAlertsMessage.className = "no-alerts-message"
      noAlertsMessage.innerHTML = `
                <i class="fas fa-check-circle text-success"></i>
                <p>Aucune alerte active</p>
            `
      tableBody.parentNode.appendChild(noAlertsMessage)
    }
  }
}

/**
 * Utilitaires
 */
function getSeverityClass(severity) {
  const classes = {
    low: "info",
    medium: "warning",
    high: "danger",
    critical: "dark",
  }
  return classes[severity] || "info"
}

// Exporter pour utilisation globale
window.AlertsApp = {
  resolveAlert,
  addNewAlertToTable,
  removeAlertFromTable,
}
