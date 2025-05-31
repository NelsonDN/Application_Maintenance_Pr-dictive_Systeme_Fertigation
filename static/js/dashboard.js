import { Chart } from "@/components/ui/chart"
/**
 * Script pour la page Dashboard avec temps réel
 */

let mainChart = null
const chartData = {}
const maxDataPoints = 50

document.addEventListener("DOMContentLoaded", () => {
  initializeDashboard()
  initializeMainChart()
  setupEventListeners()
})

/**
 * Initialise le dashboard
 */
function initializeDashboard() {
  console.log("📊 Initialisation du dashboard")

  // Initialiser les données des graphiques
  initializeChartData()

  // Charger les données initiales
  loadInitialData()
}

/**
 * Initialise les données des graphiques
 */
function initializeChartData() {
  const sensors = ["nitrogen", "phosphorus", "potassium", "water_level", "water_flow"]
  sensors.forEach((sensor) => {
    chartData[sensor] = {
      labels: [],
      data: [],
    }
  })
}

/**
 * Charge les données initiales
 */
function loadInitialData() {
  const selectedSensor = document.getElementById("main-chart-sensor").value
  loadSensorData(selectedSensor)
}

/**
 * Charge les données d'un capteur
 */
function loadSensorData(sensorName, hours = 24) {
  fetch(`/api/sensor_data/${sensorName}?hours=${hours}`)
    .then((response) => response.json())
    .then((data) => {
      chartData[sensorName] = {
        labels: data.map((item) => new Date(item.timestamp)),
        data: data.map((item) => item.value),
      }

      if (mainChart && document.getElementById("main-chart-sensor").value === sensorName) {
        updateMainChart(sensorName)
      }
    })
    .catch((error) => {
      console.error(`❌ Erreur lors du chargement des données pour ${sensorName}:`, error)
    })
}

/**
 * Initialise le graphique principal
 */
function initializeMainChart() {
  const ctx = document.getElementById("main-chart")
  if (!ctx) return

  mainChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Valeur",
          data: [],
          borderColor: "#007bff",
          backgroundColor: "rgba(0, 123, 255, 0.1)",
          borderWidth: 2,
          fill: true,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: "time",
          time: {
            displayFormats: {
              minute: "HH:mm",
              hour: "HH:mm",
            },
          },
          title: {
            display: true,
            text: "Temps",
          },
        },
        y: {
          title: {
            display: true,
            text: "Valeur",
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          mode: "index",
          intersect: false,
          callbacks: {
            title: (context) => new Date(context[0].parsed.x).toLocaleString("fr-FR"),
          },
        },
      },
      interaction: {
        mode: "nearest",
        axis: "x",
        intersect: false,
      },
    },
  })

  // Charger les données initiales
  const selectedSensor = document.getElementById("main-chart-sensor").value
  updateMainChart(selectedSensor)
}

/**
 * Met à jour le graphique principal
 */
function updateMainChart(sensorName) {
  if (!mainChart || !chartData[sensorName]) return

  const data = chartData[sensorName]

  mainChart.data.labels = data.labels
  mainChart.data.datasets[0].data = data.data
  mainChart.data.datasets[0].label = getSensorLabel(sensorName)

  // Mettre à jour la couleur selon le capteur
  const color = getSensorColor(sensorName)
  mainChart.data.datasets[0].borderColor = color
  mainChart.data.datasets[0].backgroundColor = color + "20"

  mainChart.update("none")
}

/**
 * Ajoute un nouveau point de données au graphique
 */
function addDataPoint(sensorName, timestamp, value) {
  if (!chartData[sensorName]) return

  const data = chartData[sensorName]
  const time = new Date(timestamp)

  // Ajouter le nouveau point
  data.labels.push(time)
  data.data.push(value)

  // Limiter le nombre de points
  if (data.labels.length > maxDataPoints) {
    data.labels.shift()
    data.data.shift()
  }

  // Mettre à jour le graphique si c'est le capteur sélectionné
  const selectedSensor = document.getElementById("main-chart-sensor").value
  if (sensorName === selectedSensor) {
    updateMainChart(sensorName)
  }
}

/**
 * Configure les écouteurs d'événements
 */
function setupEventListeners() {
  // Changement de capteur dans le graphique principal
  const sensorSelect = document.getElementById("main-chart-sensor")
  if (sensorSelect) {
    sensorSelect.addEventListener("change", function () {
      const selectedSensor = this.value
      loadSensorData(selectedSensor)
      updateMainChart(selectedSensor)
    })
  }

  // Écouter les mises à jour de données en temps réel
  document.addEventListener("sensorDataUpdate", (event) => {
    const data = event.detail
    addDataPoint(data.sensor_name, data.timestamp, data.value)

    // Mettre à jour les statistiques si nécessaire
    updateDashboardStats()
  })

  // Animation des cartes de capteurs
  const sensorItems = document.querySelectorAll(".sensor-item")
  sensorItems.forEach((item) => {
    item.addEventListener("mouseenter", function () {
      this.classList.add("sensor-hover")
    })

    item.addEventListener("mouseleave", function () {
      this.classList.remove("sensor-hover")
    })
  })
}

/**
 * Met à jour les statistiques du dashboard
 */
function updateDashboardStats() {
  // Cette fonction peut être étendue pour mettre à jour
  // les statistiques en temps réel si nécessaire
}

/**
 * Met à jour la liste des alertes récentes
 */
function updateRecentAlertsList() {
  fetch("/api/alerts_count")
    .then((response) => response.json())
    .then((data) => {
      // Mettre à jour le compteur d'alertes actives
      const alertsCountElement = document.getElementById("active-alerts-count")
      if (alertsCountElement) {
        alertsCountElement.textContent = data.active_count
      }
    })
    .catch((error) => {
      console.error("❌ Erreur lors de la mise à jour des alertes:", error)
    })
}

/**
 * Ajoute une alerte à la liste
 */
function addAlertToList(alert) {
  const alertsList = document.getElementById("recent-alerts-list")
  if (!alertsList) return

  // Supprimer le message "Aucune alerte" s'il existe
  const noDataMessage = alertsList.querySelector(".no-data-message")
  if (noDataMessage) {
    noDataMessage.remove()
  }

  // Créer l'élément d'alerte
  const alertElement = document.createElement("div")
  alertElement.className = "alert-item"
  alertElement.setAttribute("data-alert-id", alert.id)
  alertElement.innerHTML = `
        <div class="alert-severity alert-severity-${getSeverityClass(alert.severity)}">
            <i class="fas fa-exclamation-triangle"></i>
        </div>
        <div class="alert-content">
            <div class="alert-title">${alert.sensor_name} - ${alert.type}</div>
            <div class="alert-message">${alert.message}</div>
            <div class="alert-time">${new Date(alert.timestamp).toLocaleString("fr-FR")}</div>
        </div>
    `

  // Ajouter en haut de la liste
  alertsList.insertBefore(alertElement, alertsList.firstChild)

  // Limiter le nombre d'alertes affichées
  const alertItems = alertsList.querySelectorAll(".alert-item")
  if (alertItems.length > 5) {
    alertItems[alertItems.length - 1].remove()
  }
}

/**
 * Utilitaires
 */
function getSensorLabel(sensorName) {
  const labels = {
    nitrogen: "Azote (N)",
    phosphorus: "Phosphore (P)",
    potassium: "Potassium (K)",
    ph: "pH",
    conductivity: "Conductivité",
    temperature: "Température",
    humidity: "Humidité",
    salinity: "Salinité",
    water_level: "Niveau d'eau",
    water_temperature: "Température eau",
    water_flow: "Débit d'eau",
    water_pressure: "Pression eau",
  }
  return labels[sensorName] || sensorName
}

function getSensorColor(sensorName) {
  const colors = {
    nitrogen: "#28a745",
    phosphorus: "#ffc107",
    potassium: "#17a2b8",
    ph: "#6f42c1",
    conductivity: "#fd7e14",
    temperature: "#dc3545",
    humidity: "#20c997",
    salinity: "#6c757d",
    water_level: "#007bff",
    water_temperature: "#0dcaf0",
    water_flow: "#198754",
    water_pressure: "#0d6efd",
  }
  return colors[sensorName] || "#007bff"
}

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
window.DashboardApp = {
  addDataPoint,
  updateRecentAlertsList,
  addAlertToList,
}
