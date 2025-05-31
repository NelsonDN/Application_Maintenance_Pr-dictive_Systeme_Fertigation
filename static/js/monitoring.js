import { Chart } from "@/components/ui/chart"
/**
 * Script pour la page Monitoring avec temps réel complet
 */

// Déclaration des variables globales
const charts = {}
const chartData = {}
let isRealtimePaused = false
let refreshInterval = null
const maxDataPoints = 100
let sensorThresholds = {}

document.addEventListener("DOMContentLoaded", () => {
  initializeMonitoring()
  loadInitialData()
  setupEventListeners()
  startRealTimeUpdates()
})

/**
 * Initialise le monitoring
 */
function initializeMonitoring() {
  console.log("📊 Initialisation du monitoring temps réel")

  // Charger les seuils des capteurs
  loadSensorThresholds()

  // Initialiser les données des graphiques
  initializeChartData()

  // Créer tous les graphiques
  createAllCharts()
}

/**
 * Charge les seuils des capteurs
 */
function loadSensorThresholds() {
  const thresholdsScript = document.getElementById("sensor-thresholds")
  if (thresholdsScript) {
    try {
      sensorThresholds = JSON.parse(thresholdsScript.textContent)
    } catch (error) {
      console.error("❌ Erreur lors du chargement des seuils:", error)
    }
  }
}

/**
 * Charge les données initiales
 */
function loadInitialData() {
  const initialDataScript = document.getElementById("initial-data")
  if (initialDataScript) {
    try {
      const initialData = JSON.parse(initialDataScript.textContent)

      // Charger les données pour chaque capteur
      Object.keys(initialData).forEach((sensorName) => {
        const data = initialData[sensorName]
        if (data && data.length > 0) {
          chartData[sensorName] = {
            labels: data.map((item) => new Date(item.timestamp)),
            data: data.map((item) => item.value),
            unit: data[0].unit || "",
          }

          // Mettre à jour le graphique
          updateChart(sensorName)

          // Mettre à jour l'indicateur
          updateIndicator(sensorName, data[data.length - 1].value, data[0].unit)
        }
      })
    } catch (error) {
      console.error("❌ Erreur lors du chargement des données initiales:", error)
    }
  }
}

/**
 * Initialise les données des graphiques
 */
function initializeChartData() {
  const sensors = [
    "nitrogen",
    "phosphorus",
    "potassium",
    "ph",
    "conductivity",
    "temperature",
    "humidity",
    "salinity",
    "water_level",
    "water_temperature",
    "water_flow",
    "water_pressure",
  ]

  sensors.forEach((sensor) => {
    chartData[sensor] = {
      labels: [],
      data: [],
      unit: "",
    }
  })
}

/**
 * Crée tous les graphiques
 */
function createAllCharts() {
  const sensors = [
    "nitrogen",
    "phosphorus",
    "potassium",
    "ph",
    "conductivity",
    "temperature",
    "humidity",
    "salinity",
    "water_level",
    "water_temperature",
    "water_flow",
    "water_pressure",
  ]

  sensors.forEach((sensorName) => {
    createChart(sensorName)
  })
}

/**
 * Crée un graphique pour un capteur
 */
function createChart(sensorName) {
  const canvas = document.getElementById(`${sensorName}-chart`)
  if (!canvas) return

  const ctx = canvas.getContext("2d")
  const color = getSensorColor(sensorName)

  // Utiliser Chart directement depuis la bibliothèque chargée via CDN
  charts[sensorName] = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: getSensorLabel(sensorName),
          data: [],
          borderColor: color,
          backgroundColor: color + "20",
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 2,
          pointHoverRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 0, // Désactiver l'animation pour le temps réel
      },
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
            display: false,
          },
        },
        y: {
          title: {
            display: true,
            text: getUnit(sensorName),
          },
          beginAtZero: false,
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
            label: (context) => `${context.dataset.label}: ${context.parsed.y} ${getUnit(sensorName)}`,
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

  // Ajouter les lignes de seuil si disponibles
  addThresholdLines(sensorName)
}

/**
 * Ajoute les lignes de seuil au graphique
 */
function addThresholdLines(sensorName) {
  const chart = charts[sensorName]
  const thresholds = sensorThresholds[sensorName]

  if (!chart || !thresholds) return

  const annotations = []

  if (thresholds.min !== undefined) {
    annotations.push({
      type: "line",
      yMin: thresholds.min,
      yMax: thresholds.min,
      borderColor: "rgba(255, 99, 132, 0.8)",
      borderWidth: 2,
      borderDash: [5, 5],
      label: {
        content: `Min: ${thresholds.min}`,
        enabled: true,
        position: "start",
      },
    })
  }

  if (thresholds.max !== undefined) {
    annotations.push({
      type: "line",
      yMin: thresholds.max,
      yMax: thresholds.max,
      borderColor: "rgba(255, 99, 132, 0.8)",
      borderWidth: 2,
      borderDash: [5, 5],
      label: {
        content: `Max: ${thresholds.max}`,
        enabled: true,
        position: "start",
      },
    })
  }

  if (annotations.length > 0) {
    chart.options.plugins.annotation = {
      annotations: annotations,
    }
    chart.update()
  }
}

/**
 * Met à jour un graphique
 */
function updateChart(sensorName) {
  const chart = charts[sensorName]
  const data = chartData[sensorName]

  if (!chart || !data) return

  chart.data.labels = data.labels
  chart.data.datasets[0].data = data.data
  chart.update("none")
}

/**
 * Ajoute un point de données
 */
function addDataPoint(sensorName, timestamp, value, unit) {
  if (!chartData[sensorName]) return

  const data = chartData[sensorName]
  const time = new Date(timestamp)

  // Ajouter le nouveau point
  data.labels.push(time)
  data.data.push(value)
  data.unit = unit

  // Limiter le nombre de points
  if (data.labels.length > maxDataPoints) {
    data.labels.shift()
    data.data.shift()
  }

  // Mettre à jour le graphique
  updateChart(sensorName)

  // Mettre à jour l'indicateur
  updateIndicator(sensorName, value, unit)

  // Mettre à jour la valeur actuelle
  updateCurrentValue(sensorName, value, unit)

  // Ajouter à la table
  addToDataTable(sensorName, timestamp, value, unit)
}

/**
 * Met à jour un indicateur temps réel
 */
function updateIndicator(sensorName, value, unit) {
  const indicator = document.getElementById(`${sensorName}-indicator`)
  if (indicator) {
    indicator.textContent = `${formatNumber(value)} ${unit}`

    // Animation de mise à jour
    indicator.classList.add("updated")
    setTimeout(() => {
      indicator.classList.remove("updated")
    }, 1000)

    // Vérifier les seuils
    checkThresholds(sensorName, value, indicator)
  }
}

/**
 * Met à jour la valeur actuelle dans le titre du graphique
 */
function updateCurrentValue(sensorName, value, unit) {
  const currentElement = document.getElementById(`${sensorName}-current`)
  if (currentElement) {
    currentElement.textContent = `(${formatNumber(value)} ${unit})`
    currentElement.classList.add("updated")
    setTimeout(() => {
      currentElement.classList.remove("updated")
    }, 1000)
  }
}

/**
 * Vérifie les seuils et met à jour l'apparence
 */
function checkThresholds(sensorName, value, element) {
  const thresholds = sensorThresholds[sensorName]
  if (!thresholds || !element) return

  // Supprimer les classes existantes
  element.classList.remove("threshold-ok", "threshold-warning", "threshold-danger")

  if (value < thresholds.min || value > thresholds.max) {
    element.classList.add("threshold-danger")
  } else if (value < thresholds.min * 1.1 || value > thresholds.max * 0.9) {
    element.classList.add("threshold-warning")
  } else {
    element.classList.add("threshold-ok")
  }
}

/**
 * Ajoute une ligne à la table de données
 */
function addToDataTable(sensorName, timestamp, value, unit) {
  const tableBody = document.getElementById("data-table-body")
  if (!tableBody) return

  const row = document.createElement("tr")
  row.innerHTML = `
      <td>${new Date(timestamp).toLocaleString("fr-FR")}</td>
      <td>${getSensorLabel(sensorName)}</td>
      <td>${formatNumber(value)}</td>
      <td>${unit}</td>
      <td><span class="badge bg-success">OK</span></td>
  `

  // Ajouter en haut de la table
  tableBody.insertBefore(row, tableBody.firstChild)

  // Limiter le nombre de lignes
  const rows = tableBody.querySelectorAll("tr")
  if (rows.length > 50) {
    rows[rows.length - 1].remove()
  }
}

/**
 * Configure les écouteurs d'événements
 */
function setupEventListeners() {
  // Changement de période
  const timeRangeSelect = document.getElementById("time-range")
  if (timeRangeSelect) {
    timeRangeSelect.addEventListener("change", function () {
      const hours = Number.parseInt(this.value)
      loadDataForAllSensors(hours)
    })
  }

  // Changement de taux de rafraîchissement
  const refreshRateSelect = document.getElementById("refresh-rate")
  if (refreshRateSelect) {
    refreshRateSelect.addEventListener("change", function () {
      const rate = Number.parseInt(this.value)
      updateRefreshRate(rate)
    })
  }

  // Pause/reprise du temps réel
  const pauseButton = document.getElementById("pause-realtime")
  if (pauseButton) {
    pauseButton.addEventListener("click", () => {
      toggleRealtime()
    })
  }

  // Export des données
  const exportButton = document.getElementById("export-data")
  if (exportButton) {
    exportButton.addEventListener("click", () => {
      exportData()
    })
  }

  // Vider la table
  const clearTableButton = document.getElementById("clear-table")
  if (clearTableButton) {
    clearTableButton.addEventListener("click", () => {
      clearDataTable()
    })
  }

  // Toggle des graphiques
  const toggleButtons = document.querySelectorAll(".toggle-chart-btn")
  toggleButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const target = this.getAttribute("data-target")
      const targetElement = document.getElementById(target)
      const icon = this.querySelector("i")

      if (targetElement) {
        targetElement.style.display = targetElement.style.display === "none" ? "block" : "none"
        icon.classList.toggle("fa-chevron-up")
        icon.classList.toggle("fa-chevron-down")
      }
    })
  })

  // Écouter les mises à jour de données en temps réel
  document.addEventListener("sensorDataUpdate", (event) => {
    if (!isRealtimePaused) {
      const data = event.detail
      addDataPoint(data.sensor_name, data.timestamp, data.value, data.unit)
      updateLastDataTime()
    }
  })
}

/**
 * Démarre les mises à jour temps réel
 */
function startRealTimeUpdates() {
  updateRefreshRate(30) // Démarrer avec 30 secondes par défaut
}

/**
 * Met à jour le taux de rafraîchissement
 */
function updateRefreshRate(seconds) {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }

  if (seconds > 0) {
    refreshInterval = setInterval(() => {
      if (!isRealtimePaused) {
        // Les données arrivent via WebSocket, pas besoin de polling
        updateLastDataTime()
      }
    }, seconds * 1000)
  }
}

/**
 * Toggle du temps réel
 */
function toggleRealtime() {
  isRealtimePaused = !isRealtimePaused
  const button = document.getElementById("pause-realtime")
  const status = document.getElementById("realtime-status")

  if (isRealtimePaused) {
    button.innerHTML = '<i class="fas fa-play me-2"></i>Reprendre temps réel'
    button.className = "btn btn-outline-success"
    status.innerHTML = '<i class="fas fa-pause"></i> Temps réel en pause'
    status.className = "badge bg-warning"
  } else {
    button.innerHTML = '<i class="fas fa-pause me-2"></i>Pause temps réel'
    button.className = "btn btn-outline-warning"
    status.innerHTML = '<i class="fas fa-circle"></i> Temps réel actif'
    status.className = "badge bg-success"
  }
}

/**
 * Met à jour l'heure de dernière donnée
 */
function updateLastDataTime() {
  const lastDataElement = document.getElementById("last-data-time")
  if (lastDataElement) {
    lastDataElement.textContent = `Dernière donnée: ${new Date().toLocaleTimeString("fr-FR")}`
  }
}

/**
 * Charge les données pour tous les capteurs
 */
function loadDataForAllSensors(hours) {
  const sensors = Object.keys(chartData)

  sensors.forEach((sensorName) => {
    fetch(`/api/sensor_data/${sensorName}?hours=${hours}`)
      .then((response) => response.json())
      .then((data) => {
        chartData[sensorName] = {
          labels: data.map((item) => new Date(item.timestamp)),
          data: data.map((item) => item.value),
          unit: data.length > 0 ? data[0].unit : "",
        }
        updateChart(sensorName)

        if (data.length > 0) {
          const lastData = data[data.length - 1]
          updateIndicator(sensorName, lastData.value, lastData.unit)
          updateCurrentValue(sensorName, lastData.value, lastData.unit)
        }
      })
      .catch((error) => {
        console.error(`❌ Erreur lors du chargement des données pour ${sensorName}:`, error)
      })
  })
}

/**
 * Exporte les données
 */
function exportData() {
  const data = []

  Object.keys(chartData).forEach((sensorName) => {
    const sensorData = chartData[sensorName]
    sensorData.labels.forEach((timestamp, index) => {
      data.push({
        timestamp: timestamp.toISOString(),
        sensor: sensorName,
        value: sensorData.data[index],
        unit: sensorData.unit,
      })
    })
  })

  const csv = convertToCSV(data)
  downloadCSV(csv, "monitoring_data.csv")
}

/**
 * Convertit les données en CSV
 */
function convertToCSV(data) {
  const headers = ["Timestamp", "Sensor", "Value", "Unit"]
  const csvContent = [
    headers.join(","),
    ...data.map((row) => [row.timestamp, row.sensor, row.value, row.unit].join(",")),
  ].join("\n")

  return csvContent
}

/**
 * Télécharge un fichier CSV
 */
function downloadCSV(csv, filename) {
  const blob = new Blob([csv], { type: "text/csv" })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.setAttribute("hidden", "")
  a.setAttribute("href", url)
  a.setAttribute("download", filename)
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

/**
 * Vide la table de données
 */
function clearDataTable() {
  const tableBody = document.getElementById("data-table-body")
  if (tableBody) {
    tableBody.innerHTML = ""
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

function getUnit(sensorName) {
  const units = {
    nitrogen: "mg/kg",
    phosphorus: "mg/kg",
    potassium: "mg/kg",
    ph: "pH",
    conductivity: "µS/cm",
    temperature: "°C",
    humidity: "%",
    salinity: "ppm",
    water_level: "%",
    water_temperature: "°C",
    water_flow: "L/min",
    water_pressure: "bar",
  }
  return units[sensorName] || ""
}

function formatNumber(value) {
  return Number(value).toFixed(2)
}

// Exporter pour utilisation globale
window.MonitoringApp = {
  addDataPoint,
  toggleRealtime,
  isRealtimePaused: () => isRealtimePaused,
}
