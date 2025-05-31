/**
 * Script pour le dashboard - Version corrigée sans imports ES6
 */

// WebSocket pour temps réel
let socket = null

// Initialisation au chargement du document
document.addEventListener("DOMContentLoaded", () => {
  console.log("🔧 Initialisation du dashboard...")

  // Initialiser la connexion WebSocket
  initWebSocket()

  console.log("✅ Dashboard initialisé")
})

/**
 * Initialise la connexion WebSocket
 */
function initWebSocket() {
  console.log("🔌 Connexion WebSocket dashboard...")

  try {
    socket = io()

    socket.on("connect", () => {
      console.log("✅ WebSocket dashboard connecté")
    })

    socket.on("disconnect", () => {
      console.log("❌ WebSocket dashboard déconnecté")
    })

    // Écouter les nouvelles données de capteurs
    socket.on("sensor_data", (data) => {
      console.log("📡 Dashboard - Données capteur reçues:", data.sensor_name, data.value)
      updateDashboardSensorValue(data.sensor_name, data.value, data.unit)
    })

    socket.on("new_alert", (alert) => {
      console.log("🚨 Dashboard - Nouvelle alerte:", alert)
      updateAlertsCount()
      showDashboardAlert(alert)
    })

    socket.on("alert_resolved", (data) => {
      console.log("✅ Dashboard - Alerte résolue:", data.alert_id)
      updateAlertsCount()
    })
  } catch (error) {
    console.error("❌ Erreur WebSocket dashboard:", error)
  }
}

/**
 * Met à jour la valeur d'un capteur sur le dashboard
 */
function updateDashboardSensorValue(sensorName, value, unit) {
  console.log(`🔄 Mise à jour ${sensorName}: ${value} ${unit}`)

  // Mettre à jour la valeur dans la liste des capteurs
  const valueElement = document.getElementById(`${sensorName}-value`)
  if (valueElement) {
    valueElement.textContent = `${value} ${unit}`

    // Ajouter un effet visuel de mise à jour
    valueElement.classList.add("sensor-updated")
    setTimeout(() => {
      valueElement.classList.remove("sensor-updated")
    }, 1000)

    console.log(`✅ Valeur mise à jour pour ${sensorName}`)
  } else {
    console.warn(`⚠️ Élément non trouvé pour ${sensorName}`)
  }

  // Mettre à jour le statut du capteur
  const statusElement = document.getElementById(`${sensorName}-status`)
  if (statusElement) {
    const icon = statusElement.querySelector("i")
    if (icon) {
      // Changer temporairement la couleur pour indiquer une mise à jour
      icon.className = "fas fa-circle text-primary"
      setTimeout(() => {
        icon.className = "fas fa-circle text-success"
      }, 500)
    }
  }
}

/**
 * Met à jour le compteur d'alertes
 */
function updateAlertsCount() {
  // Recharger le compteur d'alertes depuis l'API
  fetch("/api/alerts_count")
    .then((response) => response.json())
    .then((data) => {
      const alertsCountElement = document.querySelector(".stat-card .bg-warning + .stat-content h3")
      if (alertsCountElement) {
        alertsCountElement.textContent = data.active_count
      }
    })
    .catch((error) => {
      console.error("❌ Erreur mise à jour compteur alertes:", error)
    })
}

/**
 * Affiche une alerte sur le dashboard
 */
function showDashboardAlert(alert) {
  // Créer une notification toast
  const toast = document.createElement("div")
  toast.className = "toast align-items-center text-white bg-warning border-0"
  toast.setAttribute("role", "alert")
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <strong>Nouvelle alerte!</strong><br>
        ${alert.message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `

  // Ajouter au container de toasts
  let toastContainer = document.getElementById("toast-container")
  if (!toastContainer) {
    toastContainer = document.createElement("div")
    toastContainer.id = "toast-container"
    toastContainer.className = "toast-container position-fixed top-0 end-0 p-3"
    document.body.appendChild(toastContainer)
  }

  toastContainer.appendChild(toast)

  // Initialiser et afficher le toast
  const bsToast = new bootstrap.Toast(toast)
  bsToast.show()

  // Supprimer après fermeture
  toast.addEventListener("hidden.bs.toast", () => {
    toast.remove()
  })
}

// Démarrage automatique
console.log("📊 Script dashboard chargé")
