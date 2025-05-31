import { Chart } from "@/components/ui/chart"
/**
 * Script pour la page de maintenance
 */

// Graphique des coûts de maintenance
let costsChart = null

// Initialisation au chargement du document
document.addEventListener("DOMContentLoaded", () => {
  // Initialiser le graphique des coûts
  initCostsChart()

  // Configurer les boutons d'action
  setupActionButtons()

  // Configurer les formulaires de mise à jour de statut
  setupStatusForms()
})

/**
 * Initialise le graphique des coûts de maintenance
 */
function initCostsChart() {
  const canvas = document.getElementById("maintenance-costs-chart")
  if (!canvas) return

  costsChart = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: ["Maintenance préventive", "Maintenance corrective", "Économies réalisées"],
      datasets: [
        {
          data: [60, 25, 15],
          backgroundColor: ["#27ae60", "#e74c3c", "#3498db"],
          borderWidth: 2,
          borderColor: "#fff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            padding: 20,
            usePointStyle: true,
          },
        },
        tooltip: {
          callbacks: {
            label: (context) => `${context.label}: ${context.parsed}%`,
          },
        },
      },
    },
  })
}

/**
 * Configure les boutons d'action
 */
function setupActionButtons() {
  // Bouton d'analyse prédictive
  const runAnalysisBtn = document.getElementById("run-analysis-btn")
  if (runAnalysisBtn) {
    runAnalysisBtn.addEventListener("click", runPredictiveAnalysis)
  }

  // Bouton de planification de maintenance
  const scheduleBtn = document.getElementById("schedule-maintenance-btn")
  if (scheduleBtn) {
    scheduleBtn.addEventListener("click", showScheduleMaintenanceModal)
  }

  // Bouton d'export
  const exportBtn = document.getElementById("export-maintenance-btn")
  if (exportBtn) {
    exportBtn.addEventListener("click", exportMaintenanceReport)
  }
}

/**
 * Configure les formulaires de mise à jour de statut
 */
function setupStatusForms() {
  const forms = document.querySelectorAll('form[action*="update_maintenance"]')

  forms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      const status = this.querySelector('input[name="status"]').value

      if (status === "cancelled") {
        if (!confirm("Êtes-vous sûr de vouloir annuler cette maintenance ?")) {
          e.preventDefault()
          return
        }
      } else if (status === "completed") {
        if (!confirm("Marquer cette maintenance comme terminée ?")) {
          e.preventDefault()
          return
        }
      }
    })
  })
}

/**
 * Lance l'analyse prédictive
 */
function runPredictiveAnalysis() {
  const button = document.getElementById("run-analysis-btn")

  // Désactiver le bouton et afficher le spinner
  button.disabled = true
  button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyse en cours...'

  fetch("/api/run_predictive_analysis", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      showNotification("Analyse prédictive terminée avec succès", "success")

      // Recharger la page pour afficher les nouveaux résultats
      setTimeout(() => {
        window.location.reload()
      }, 1500)
    })
    .catch((error) => {
      console.error("Erreur:", error)
      showNotification("Erreur lors de l'analyse prédictive", "danger")
    })
    .finally(() => {
      // Réactiver le bouton
      button.disabled = false
      button.innerHTML = '<i class="fas fa-brain me-2"></i>Lancer l\'analyse prédictive'
    })
}

/**
 * Affiche le modal de planification de maintenance
 */
function showScheduleMaintenanceModal() {
  // Créer le modal dynamiquement
  const modalHTML = `
        <div class="modal fade" id="schedule-maintenance-modal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Planifier une maintenance</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="schedule-maintenance-form">
                            <div class="mb-3">
                                <label for="maintenance-sensor" class="form-label">Capteur</label>
                                <select id="maintenance-sensor" name="sensor_name" class="form-select" required>
                                    <option value="">Sélectionner un capteur</option>
                                    <option value="nitrogen">Azote (N)</option>
                                    <option value="phosphorus">Phosphore (P)</option>
                                    <option value="potassium">Potassium (K)</option>
                                    <option value="ph">pH</option>
                                    <option value="water_level">Niveau d'eau</option>
                                    <option value="water_flow">Débit d'eau</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label for="maintenance-type" class="form-label">Type de maintenance</label>
                                <select id="maintenance-type" name="maintenance_type" class="form-select" required>
                                    <option value="">Sélectionner un type</option>
                                    <option value="preventive">Préventive</option>
                                    <option value="corrective">Corrective</option>
                                    <option value="predictive">Prédictive</option>
                                    <option value="emergency">Urgence</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label for="maintenance-date" class="form-label">Date planifiée</label>
                                <input type="datetime-local" id="maintenance-date" name="scheduled_date" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label for="maintenance-description" class="form-label">Description</label>
                                <textarea id="maintenance-description" name="description" class="form-control" rows="3" required></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="button" class="btn btn-primary" id="confirm-schedule-maintenance">Planifier</button>
                    </div>
                </div>
            </div>
        </div>
    `

  // Ajouter le modal au document
  document.body.insertAdjacentHTML("beforeend", modalHTML)

  // Afficher le modal
  const modalElement = document.getElementById("schedule-maintenance-modal")
  const modal = new bootstrap.Modal(modalElement)
  modal.show()

  // Configurer la date minimale (maintenant)
  const dateInput = document.getElementById("maintenance-date")
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  dateInput.min = now.toISOString().slice(0, 16)

  // Configurer le bouton de confirmation
  document.getElementById("confirm-schedule-maintenance").addEventListener("click", scheduleMaintenanceFromModal)

  // Nettoyer le modal après fermeture
  modalElement.addEventListener("hidden.bs.modal", function () {
    this.remove()
  })
}

/**
 * Planifie une maintenance depuis le modal
 */
function scheduleMaintenanceFromModal() {
  const form = document.getElementById("schedule-maintenance-form")
  const formData = new FormData(form)

  // Valider le formulaire
  if (!form.checkValidity()) {
    form.reportValidity()
    return
  }

  // Simuler la création de la maintenance
  // Dans une vraie application, on enverrait les données au serveur
  showNotification("Maintenance planifiée avec succès", "success")

  // Fermer le modal
  const modal = bootstrap.Modal.getInstance(document.getElementById("schedule-maintenance-modal"))
  modal.hide()

  // Recharger la page après un délai
  setTimeout(() => {
    window.location.reload()
  }, 1500)
}

/**
 * Exporte le rapport de maintenance
 */
function exportMaintenanceReport() {
  // Collecter les données de maintenance
  const maintenanceData = []

  // Récupérer toutes les maintenances affichées
  const maintenanceItems = document.querySelectorAll(".maintenance-item")

  maintenanceItems.forEach((item) => {
    const title = item.querySelector(".maintenance-title")?.textContent || ""
    const type = item.querySelector(".maintenance-type")?.textContent || ""
    const description = item.querySelector(".maintenance-description")?.textContent || ""
    const date = item.querySelector(".maintenance-date")?.textContent || ""
    const status = item.querySelector(".badge")?.textContent || ""

    maintenanceData.push({
      Capteur: title,
      Type: type,
      Description: description,
      Date: date.replace("Planifiée pour: ", "").replace("Démarrée: ", "").replace("Terminée: ", ""),
      Statut: status,
    })
  })

  if (maintenanceData.length === 0) {
    showNotification("Aucune maintenance à exporter", "info")
    return
  }

  const filename = `rapport_maintenance_${new Date().toISOString().split("T")[0]}.csv`
  exportToCSV(maintenanceData, filename)
  showNotification(`Rapport de maintenance exporté (${maintenanceData.length} entrées)`, "success")
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
 * Exporte les données au format CSV
 */
function exportToCSV(data, filename) {
  const csvRows = []

  // En-têtes
  const headers = Object.keys(data[0])
  csvRows.push(headers.join(","))

  // Lignes de données
  for (const row of data) {
    const values = headers.map((header) => {
      const value = row[header]
      return `"${value.replace(/"/g, '""')}"` // Échapper les guillemets
    })
    csvRows.push(values.join(","))
  }

  // Créer le contenu CSV
  const csvContent = csvRows.join("\n")

  // Créer un lien de téléchargement
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)

  // Créer un élément <a> pour déclencher le téléchargement
  const link = document.createElement("a")
  link.href = url
  link.setAttribute("download", filename)
  document.body.appendChild(link)

  // Déclencher le téléchargement
  link.click()

  // Nettoyer
  document.body.removeChild(link)
}
