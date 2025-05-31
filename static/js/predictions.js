import { Chart } from "@/components/ui/chart"
import * as bootstrap from "bootstrap"
/**
 * Script pour la page de prédictions
 */

// Graphique de tendance des risques
let riskTrendChart = null

// Initialisation au chargement du document
document.addEventListener("DOMContentLoaded", () => {
  // Initialiser le graphique de tendance des risques
  initRiskTrendChart()

  // Configurer les boutons de recommandations
  setupRecommendationButtons()

  // Configurer le bouton d'export
  setupExportButton()

  // Configurer le bouton de planification depuis le modal
  setupScheduleFromModal()
})

/**
 * Initialise le graphique de tendance des risques
 */
function initRiskTrendChart() {
  const canvas = document.getElementById("risk-trend-chart")
  if (!canvas) return

  // Générer des données de tendance simulées
  const labels = []
  const datasets = []

  // Créer des dates pour les 30 derniers jours
  for (let i = 30; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    labels.push(date)
  }

  // Créer des données pour quelques capteurs
  const sensorNames = ["Azote (N)", "Phosphore (P)", "Potassium (K)", "Niveau d'eau", "Débit d'eau"]
  const colors = ["#3498db", "#2ecc71", "#e74c3c", "#9b59b6", "#f39c12"]

  sensorNames.forEach((sensor, index) => {
    // Générer une tendance de risque avec une légère augmentation
    const data = []
    let value = Math.random() * 0.2 + 0.1 // Valeur initiale entre 0.1 et 0.3

    for (let i = 0; i <= 30; i++) {
      // Ajouter une tendance croissante avec du bruit
      value += Math.random() * 0.03 - 0.01
      // Limiter entre 0 et 1
      value = Math.max(0, Math.min(1, value))
      data.push(value)
    }

    datasets.push({
      label: sensor,
      data: data,
      borderColor: colors[index],
      backgroundColor: colors[index] + "20",
      borderWidth: 2,
      tension: 0.3,
      fill: false,
      pointRadius: 2,
    })
  })

  riskTrendChart = new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
        },
        tooltip: {
          mode: "index",
          intersect: false,
          callbacks: {
            label: (context) => {
              const value = context.parsed.y * 100
              return `${context.dataset.label}: ${value.toFixed(1)}% de risque`
            },
          },
        },
      },
      scales: {
        x: {
          type: "time",
          time: {
            unit: "day",
            displayFormats: {
              day: "dd/MM",
            },
          },
          title: {
            display: true,
            text: "Date",
          },
        },
        y: {
          beginAtZero: true,
          max: 1,
          title: {
            display: true,
            text: "Probabilité de défaillance",
          },
          ticks: {
            callback: (value) => `${(value * 100).toFixed(0)}%`,
          },
        },
      },
    },
  })
}

/**
 * Configure les boutons de recommandations
 */
function setupRecommendationButtons() {
  const recommendationButtons = document.querySelectorAll(".view-recommendations-btn")

  recommendationButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const sensorName = this.getAttribute("data-sensor")
      showRecommendationsModal(sensorName)
    })
  })
}

/**
 * Configure le bouton d'export
 */
function setupExportButton() {
  const exportButton = document.getElementById("export-predictions-btn")
  if (exportButton) {
    exportButton.addEventListener("click", exportPredictionsReport)
  }
}

/**
 * Configure le bouton de planification depuis le modal
 */
function setupScheduleFromModal() {
  document.addEventListener("click", (e) => {
    if (e.target && e.target.id === "schedule-maintenance-from-modal") {
      scheduleMaintenance()
    }
  })
}

/**
 * Affiche le modal de recommandations
 */
function showRecommendationsModal(sensorName) {
  // Récupérer les recommandations pour ce capteur
  // Dans une vraie application, on pourrait les récupérer via une API
  const recommendations = getRecommendationsForSensor(sensorName)

  // Créer le contenu du modal
  const modalContent = document.getElementById("recommendations-content")
  if (!modalContent) return

  modalContent.innerHTML = `
        <div class="recommendations-detail">
            <h6 class="mb-3">Recommandations pour ${sensorName}</h6>
            
            <div class="sensor-status mb-4">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="fw-bold">État actuel:</span>
                    <span class="badge bg-warning">Risque moyen</span>
                </div>
                <div class="progress" style="height: 10px;">
                    <div class="progress-bar bg-warning" role="progressbar" style="width: 65%;" 
                        aria-valuenow="65" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
                <div class="d-flex justify-content-between mt-1">
                    <small>Probabilité de défaillance: 65%</small>
                    <small>Jours restants estimés: 42</small>
                </div>
            </div>
            
            <h6 class="mb-3">Actions recommandées</h6>
            <div class="recommendations-list">
                ${recommendations
                  .map(
                    (rec) => `
                    <div class="recommendation-item recommendation-${rec.priority.toLowerCase()}">
                        <div class="recommendation-icon">
                            <i class="fas ${getIconForRecommendationType(rec.type)}"></i>
                        </div>
                        <div class="recommendation-content">
                            <div class="recommendation-title">${rec.title}</div>
                            <div class="recommendation-description">${rec.description}</div>
                            <div class="recommendation-priority">
                                <span class="badge bg-${getPriorityClass(rec.priority)}">
                                    ${rec.priority}
                                </span>
                            </div>
                        </div>
                    </div>
                `,
                  )
                  .join("")}
            </div>
            
            <h6 class="mt-4 mb-3">Historique des maintenances</h6>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>15/11/2023</td>
                            <td>Préventive</td>
                            <td>Étalonnage du capteur</td>
                        </tr>
                        <tr>
                            <td>03/09/2023</td>
                            <td>Corrective</td>
                            <td>Remplacement du filtre</td>
                        </tr>
                        <tr>
                            <td>22/06/2023</td>
                            <td>Préventive</td>
                            <td>Nettoyage du système</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `

  // Afficher le modal
  const modal = new bootstrap.Modal(document.getElementById("recommendations-modal"))
  modal.show()

  // Stocker le nom du capteur dans le bouton de planification
  const scheduleButton = document.getElementById("schedule-maintenance-from-modal")
  if (scheduleButton) {
    scheduleButton.setAttribute("data-sensor", sensorName)
  }
}

/**
 * Planifie une maintenance depuis le modal de recommandations
 */
function scheduleMaintenance() {
  const scheduleButton = document.getElementById("schedule-maintenance-from-modal")
  const sensorName = scheduleButton.getAttribute("data-sensor")

  // Fermer le modal actuel
  const currentModal = bootstrap.Modal.getInstance(document.getElementById("recommendations-modal"))
  currentModal.hide()

  // Créer le modal de planification
  const modalHTML = `
        <div class="modal fade" id="schedule-maintenance-modal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Planifier une maintenance pour ${sensorName}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="schedule-maintenance-form">
                            <input type="hidden" name="sensor_name" value="${sensorName}">
                            <div class="mb-3">
                                <label for="maintenance-type" class="form-label">Type de maintenance</label>
                                <select id="maintenance-type" name="maintenance_type" class="form-select" required>
                                    <option value="preventive">Préventive</option>
                                    <option value="predictive" selected>Prédictive</option>
                                    <option value="corrective">Corrective</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label for="maintenance-date" class="form-label">Date planifiée</label>
                                <input type="datetime-local" id="maintenance-date" name="scheduled_date" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label for="maintenance-description" class="form-label">Description</label>
                                <textarea id="maintenance-description" name="description" class="form-control" rows="3" required>Maintenance prédictive basée sur l'analyse de risque</textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="button" class="btn btn-primary" id="confirm-schedule">Planifier</button>
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

  // Configurer la date par défaut (demain)
  const dateInput = document.getElementById("maintenance-date")
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setMinutes(tomorrow.getMinutes() - tomorrow.getTimezoneOffset())
  dateInput.value = tomorrow.toISOString().slice(0, 16)

  // Configurer le bouton de confirmation
  document.getElementById("confirm-schedule").addEventListener("click", confirmScheduleMaintenance)

  // Nettoyer le modal après fermeture
  modalElement.addEventListener("hidden.bs.modal", function () {
    this.remove()
  })
}

/**
 * Confirme la planification d'une maintenance
 */
function confirmScheduleMaintenance() {
  const form = document.getElementById("schedule-maintenance-form")

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

  // Rediriger vers la page de maintenance après un délai
  setTimeout(() => {
    window.location.href = "/maintenance"
  }, 1500)
}

/**
 * Exporte le rapport de prédictions
 */
function exportPredictionsReport() {
  // Collecter les données de prédiction
  const predictionData = []

  // Récupérer toutes les cartes de prédiction
  const predictionCards = document.querySelectorAll(".prediction-card")

  predictionCards.forEach((card) => {
    const sensor = card.querySelector(".prediction-sensor")?.textContent || ""
    const risk = card.querySelector(".prediction-risk")?.textContent || ""
    const failureProb = card.querySelector(".gauge-value")?.textContent || ""
    const failureDate = card.querySelector(".detail-row:nth-child(1) .detail-value")?.textContent?.trim() || ""
    const daysLeft = card.querySelector(".detail-row:nth-child(2) .detail-value")?.textContent?.trim() || ""
    const confidence = card.querySelector(".detail-row:nth-child(3) .detail-value")?.textContent?.trim() || ""

    predictionData.push({
      Capteur: sensor,
      "Niveau de risque": risk,
      "Probabilité de défaillance": failureProb,
      "Date de défaillance prévue": failureDate,
      "Jours restants": daysLeft,
      Confiance: confidence,
    })
  })

  if (predictionData.length === 0) {
    showNotification("Aucune prédiction à exporter", "info")
    return
  }

  const filename = `predictions_${new Date().toISOString().split("T")[0]}.csv`
  exportToCSV(predictionData, filename)
  showNotification(`Rapport de prédictions exporté (${predictionData.length} entrées)`, "success")
}

/**
 * Retourne les recommandations pour un capteur
 */
function getRecommendationsForSensor(sensorName) {
  // Simuler des recommandations différentes selon le capteur
  const recommendations = []

  // Recommandations communes
  recommendations.push({
    title: "Planifier une maintenance préventive",
    description: "Planifier une maintenance préventive dans les 30 prochains jours pour éviter une défaillance.",
    type: "PREVENTIVE",
    priority: "MEDIUM",
  })

  // Recommandations spécifiques
  switch (sensorName) {
    case "Azote (N)":
      recommendations.push({
        title: "Vérifier le système de dosage",
        description: "Inspecter le système de dosage d'azote pour détecter d'éventuelles fuites ou obstructions.",
        type: "PREVENTIVE",
        priority: "HIGH",
      })
      recommendations.push({
        title: "Étalonner le capteur",
        description: "Effectuer un étalonnage complet du capteur d'azote pour assurer des mesures précises.",
        type: "PREVENTIVE",
        priority: "MEDIUM",
      })
      break

    case "Phosphore (P)":
      recommendations.push({
        title: "Nettoyer les filtres",
        description: "Nettoyer les filtres du système de distribution de phosphore pour éviter les obstructions.",
        type: "PREVENTIVE",
        priority: "HIGH",
      })
      recommendations.push({
        title: "Vérifier les vannes",
        description: "Contrôler le bon fonctionnement des vannes de régulation du phosphore.",
        type: "PREVENTIVE",
        priority: "MEDIUM",
      })
      break

    case "Potassium (K)":
      recommendations.push({
        title: "Remplacer le capteur",
        description: "Le capteur de potassium approche de sa fin de vie. Prévoir un remplacement.",
        type: "REPLACEMENT",
        priority: "CRITICAL",
      })
      recommendations.push({
        title: "Vérifier le circuit électrique",
        description: "Contrôler les connexions électriques du capteur de potassium.",
        type: "PREVENTIVE",
        priority: "LOW",
      })
      break

    case "pH":
      recommendations.push({
        title: "Étalonner le capteur de pH",
        description: "Effectuer un étalonnage avec des solutions tampons standard.",
        type: "PREVENTIVE",
        priority: "HIGH",
      })
      recommendations.push({
        title: "Nettoyer l'électrode",
        description: "Nettoyer l'électrode de pH avec une solution appropriée pour éliminer les dépôts.",
        type: "PREVENTIVE",
        priority: "MEDIUM",
      })
      break

    case "Niveau d'eau":
      recommendations.push({
        title: "Vérifier le flotteur",
        description: "Contrôler le mécanisme du flotteur pour assurer une mesure précise du niveau d'eau.",
        type: "PREVENTIVE",
        priority: "MEDIUM",
      })
      recommendations.push({
        title: "Nettoyer le capteur",
        description: "Éliminer les dépôts minéraux qui peuvent affecter la précision du capteur.",
        type: "PREVENTIVE",
        priority: "LOW",
      })
      break

    case "Débit d'eau":
      recommendations.push({
        title: "Intervention d'urgence requise",
        description:
          "Le capteur de débit montre des signes de défaillance imminente. Une intervention rapide est nécessaire.",
        type: "EMERGENCY",
        priority: "CRITICAL",
      })
      recommendations.push({
        title: "Vérifier les obstructions",
        description: "Rechercher d'éventuelles obstructions dans le circuit qui pourraient affecter le débit.",
        type: "PREVENTIVE",
        priority: "HIGH",
      })
      break

    default:
      recommendations.push({
        title: "Inspection générale",
        description: "Effectuer une inspection visuelle du capteur et de ses connexions.",
        type: "PREVENTIVE",
        priority: "MEDIUM",
      })
  }

  return recommendations
}

/**
 * Retourne l'icône pour un type de recommandation
 */
function getIconForRecommendationType(type) {
  switch (type) {
    case "PREVENTIVE":
      return "fa-shield-alt"
    case "URGENT":
      return "fa-exclamation-triangle"
    case "EMERGENCY":
      return "fa-bolt"
    case "REPLACEMENT":
      return "fa-exchange-alt"
    default:
      return "fa-info-circle"
  }
}

/**
 * Retourne la classe CSS pour une priorité
 */
function getPriorityClass(priority) {
  switch (priority.toLowerCase()) {
    case "critical":
      return "danger"
    case "high":
      return "warning"
    case "medium":
      return "info"
    case "low":
      return "secondary"
    default:
      return "secondary"
  }
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
      const value = row[header] || ""
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
