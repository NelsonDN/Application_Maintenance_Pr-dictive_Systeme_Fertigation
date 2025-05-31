/**
 * Script pour la page d'alertes
 */

// Initialisation au chargement du document
document.addEventListener("DOMContentLoaded", () => {
  // Configurer les boutons de résolution d'alertes
  setupResolveButtons()

  // Configurer les boutons de détails
  setupDetailsButtons()

  // Configurer les actions globales
  setupGlobalActions()

  // Configurer le modal de test d'anomalie
  setupForceAnomalyModal()

  // Écouter les nouvelles alertes
  document.addEventListener("new-alert", (event) => {
    addNewAlertToList(event.detail)
  })
})

/**
 * Configure les boutons de résolution d'alertes
 */
function setupResolveButtons() {
  const resolveButtons = document.querySelectorAll(".resolve-alert-btn")

  resolveButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const alertId = this.getAttribute("data-alert-id")
      resolveAlert(alertId, this)
    })
  })
}

/**
 * Configure les boutons de détails
 */
function setupDetailsButtons() {
  const detailsButtons = document.querySelectorAll(".view-details-btn")

  detailsButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const alertId = this.getAttribute("data-alert-id")
      showAlertDetails(alertId)
    })
  })
}

/**
 * Configure les actions globales
 */
function setupGlobalActions() {
  // Résoudre toutes les alertes
  const resolveAllBtn = document.getElementById("resolve-all-btn")
  if (resolveAllBtn) {
    resolveAllBtn.addEventListener("click", resolveAllAlerts)
  }

  // Exporter les alertes
  const exportBtn = document.getElementById("export-alerts-btn")
  if (exportBtn) {
    exportBtn.addEventListener("click", exportAlerts)
  }

  // Forcer une anomalie
  const forceAnomalyBtn = document.getElementById("force-anomaly-btn")
  if (forceAnomalyBtn) {
    forceAnomalyBtn.addEventListener("click", () => {
      const modal = new bootstrap.Modal(document.getElementById("force-anomaly-modal"))
      modal.show()
    })
  }
}

/**
 * Configure le modal de test d'anomalie
 */
function setupForceAnomalyModal() {
  const confirmBtn = document.getElementById("confirm-force-anomaly")
  if (confirmBtn) {
    confirmBtn.addEventListener("click", forceAnomaly)
  }
}

/**
 * Résout une alerte spécifique
 */
function resolveAlert(alertId, buttonElement) {
  // Désactiver le bouton pendant la requête
  buttonElement.disabled = true
  buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Résolution...'

  fetch(`/alerts/resolve/${alertId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Supprimer l'alerte de la liste active
        const alertItem = buttonElement.closest(".alert-item")
        if (alertItem) {
          alertItem.style.transition = "opacity 0.3s ease"
          alertItem.style.opacity = "0"
          setTimeout(() => {
            alertItem.remove()
            updateAlertCounts()
          }, 300)
        }

        // Afficher un message de succès
        showNotification("Alerte résolue avec succès", "success")
      } else {
        throw new Error("Erreur lors de la résolution de l'alerte")
      }
    })
    .catch((error) => {
      console.error("Erreur:", error)
      showNotification("Erreur lors de la résolution de l'alerte", "danger")

      // Réactiver le bouton
      buttonElement.disabled = false
      buttonElement.innerHTML = '<i class="fas fa-check"></i> Résoudre'
    })
}

/**
 * Résout toutes les alertes actives
 */
function resolveAllAlerts() {
  const activeAlerts = document.querySelectorAll("#active-alerts .resolve-alert-btn")

  if (activeAlerts.length === 0) {
    showNotification("Aucune alerte active à résoudre", "info")
    return
  }

  if (!confirm(`Êtes-vous sûr de vouloir résoudre toutes les ${activeAlerts.length} alertes actives ?`)) {
    return
  }

  // Résoudre chaque alerte
  activeAlerts.forEach((button) => {
    const alertId = button.getAttribute("data-alert-id")
    resolveAlert(alertId, button)
  })
}

/**
 * Affiche les détails d'une alerte
 */
function showAlertDetails(alertId) {
  // Pour l'instant, afficher un modal simple
  // Dans une implémentation complète, on récupérerait les détails via API
  const modal = document.getElementById("alert-details-modal")
  const content = document.getElementById("alert-details-content")

  content.innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Chargement...</span>
            </div>
            <p class="mt-2">Chargement des détails de l'alerte...</p>
        </div>
    `

  const bootstrapModal = new bootstrap.Modal(modal)
  bootstrapModal.show()

  // Simuler le chargement des détails
  setTimeout(() => {
    content.innerHTML = `
            <div class="alert-details">
                <h6>Détails de l'alerte #${alertId}</h6>
                <div class="row">
                    <div class="col-md-6">
                        <strong>Capteur:</strong> Azote (N)<br>
                        <strong>Type:</strong> Seuil dépassé<br>
                        <strong>Sévérité:</strong> <span class="badge bg-warning">MOYENNE</span><br>
                        <strong>Créée le:</strong> ${new Date().toLocaleString("fr-FR")}
                    </div>
                    <div class="col-md-6">
                        <strong>Valeur mesurée:</strong> 650 mg/kg<br>
                        <strong>Seuil maximum:</strong> 600 mg/kg<br>
                        <strong>Écart:</strong> +8.3%<br>
                        <strong>Statut:</strong> <span class="badge bg-danger">ACTIVE</span>
                    </div>
                </div>
                <hr>
                <h6>Historique des valeurs</h6>
                <div class="chart-container" style="height: 200px;">
                    <canvas id="alert-detail-chart"></canvas>
                </div>
                <hr>
                <h6>Actions recommandées</h6>
                <ul>
                    <li>Vérifier le système de dosage d'azote</li>
                    <li>Contrôler les vannes de distribution</li>
                    <li>Effectuer un étalonnage du capteur</li>
                </ul>
            </div>
        `
  }, 1000)
}

/**
 * Exporte les alertes au format CSV
 */
function exportAlerts() {
  const alertItems = document.querySelectorAll(".alert-item")
  const alertsData = []

  alertItems.forEach((item) => {
    const title = item.querySelector(".alert-title")?.textContent || ""
    const message = item.querySelector(".alert-message")?.textContent || ""
    const time = item.querySelector(".alert-time")?.textContent || ""
    const severity = item.querySelector(".severity-text")?.textContent || ""

    alertsData.push({
      "Date/Heure": time,
      Capteur: title.split(" - ")[0] || "",
      Type: title.split(" - ")[1] || "",
      Message: message,
      Sévérité: severity,
    })
  })

  if (alertsData.length === 0) {
    showNotification("Aucune alerte à exporter", "info")
    return
  }

  const filename = `alertes_${new Date().toISOString().split("T")[0]}.csv`
  exportToCSV(alertsData, filename)
  showNotification(`${alertsData.length} alertes exportées`, "success")
}

/**
 * Force une anomalie pour les tests
 */
function forceAnomaly() {
  const form = document.getElementById("force-anomaly-form")
  const formData = new FormData(form)

  const sensorName = formData.get("sensor_name")
  const anomalyType = formData.get("anomaly_type")

  if (!sensorName || !anomalyType) {
    showNotification("Veuillez sélectionner un capteur et un type d'anomalie", "warning")
    return
  }

  fetch("/api/force_anomaly", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Anomalie forcée avec succès", "success")

        // Fermer le modal
        const modal = bootstrap.Modal.getInstance(document.getElementById("force-anomaly-modal"))
        modal.hide()

        // Réinitialiser le formulaire
        form.reset()
      } else {
        throw new Error("Erreur lors de la création de l'anomalie")
      }
    })
    .catch((error) => {
      console.error("Erreur:", error)
      showNotification("Erreur lors de la création de l'anomalie", "danger")
    })
}

/**
 * Ajoute une nouvelle alerte à la liste
 */
function addNewAlertToList(alert) {
  const activeAlertsContainer = document.querySelector("#active-alerts .alerts-list")
  if (!activeAlertsContainer) return

  // Créer l'élément d'alerte
  const alertElement = document.createElement("div")
  alertElement.className = "alert-item"
  alertElement.setAttribute("data-alert-id", alert.id)

  alertElement.innerHTML = `
        <div class="alert-severity alert-severity-${getSeverityClass(alert.severity)}">
            <i class="fas fa-exclamation-triangle"></i>
            <span class="severity-text">${alert.severity.toUpperCase()}</span>
        </div>
        <div class="alert-content">
            <div class="alert-header">
                <h6 class="alert-title">${alert.sensor_name} - ${alert.type}</h6>
                <div class="alert-time">
                    <i class="far fa-clock"></i>
                    ${formatDate(alert.timestamp)}
                </div>
            </div>
            <div class="alert-message">${alert.message}</div>
        </div>
        <div class="alert-actions">
            <button class="btn btn-sm btn-success resolve-alert-btn" data-alert-id="${alert.id}">
                <i class="fas fa-check"></i>
                Résoudre
            </button>
            <button class="btn btn-sm btn-outline-info view-details-btn" data-alert-id="${alert.id}">
                <i class="fas fa-info-circle"></i>
                Détails
            </button>
        </div>
    `

  // Ajouter l'animation d'entrée
  alertElement.style.opacity = "0"
  alertElement.style.transform = "translateY(-20px)"

  // Insérer au début de la liste
  activeAlertsContainer.insertBefore(alertElement, activeAlertsContainer.firstChild)

  // Animer l'entrée
  setTimeout(() => {
    alertElement.style.transition = "all 0.3s ease"
    alertElement.style.opacity = "1"
    alertElement.style.transform = "translateY(0)"
  }, 100)

  // Configurer les boutons de la nouvelle alerte
  const resolveBtn = alertElement.querySelector(".resolve-alert-btn")
  const detailsBtn = alertElement.querySelector(".view-details-btn")

  resolveBtn.addEventListener("click", function () {
    resolveAlert(alert.id, this)
  })

  detailsBtn.addEventListener("click", () => {
    showAlertDetails(alert.id)
  })

  // Mettre à jour les compteurs
  updateAlertCounts()
}

/**
 * Met à jour les compteurs d'alertes
 */
function updateAlertCounts() {
  const activeCount = document.querySelectorAll("#active-alerts .alert-item").length
  const resolvedCount = document.querySelectorAll("#resolved-alerts .alert-item").length

  // Mettre à jour les badges des onglets
  const activeTab = document.querySelector("#active-tab .badge")
  const resolvedTab = document.querySelector("#resolved-tab .badge")

  if (activeTab) activeTab.textContent = activeCount
  if (resolvedTab) resolvedTab.textContent = resolvedCount

  // Mettre à jour le badge de la sidebar
  const sidebarBadge = document.getElementById("alerts-badge")
  if (sidebarBadge) {
    if (activeCount > 0) {
      sidebarBadge.textContent = activeCount
      sidebarBadge.classList.remove("d-none")
    } else {
      sidebarBadge.classList.add("d-none")
    }
  }
}

/**
 * Retourne la classe CSS pour une sévérité
 */
function getSeverityClass(severity) {
  const classes = {
    low: "info",
    medium: "warning",
    high: "danger",
    critical: "dark",
  }

  return classes[severity.toLowerCase()] || "info"
}

/**
 * Affiche une notification
 */
function showNotification(message, type = "info") {
  // Créer l'élément de notification
  const notification = document.createElement("div")
  notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`
  notification.style.cssText = "top: 20px; right: 20px; z-index: 9999; min-width: 300px;"

  notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `

  // Ajouter au document
  document.body.appendChild(notification)

  // Supprimer automatiquement après 5 secondes
  setTimeout(() => {
    if (notification.parentNode) {
      notification.remove()
    }
  }, 5000)
}

/**
 * Formate une date pour l'affichage
 */
function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleString("fr-FR")
}

// Declare bootstrap and exportToCSV to avoid linting errors
const bootstrap = window.bootstrap
const exportToCSV = window.exportToCSV
