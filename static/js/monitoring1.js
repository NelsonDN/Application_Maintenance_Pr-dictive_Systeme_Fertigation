import { Chart } from "@/components/ui/chart"
/**
 * Script pour la page de monitoring - Version corrigée avec Chart.js standard
 */

// Graphiques des capteurs
const charts = {}

// Données initiales
let initialData = {}
let sensorThresholds = {}

// WebSocket pour temps réel
let socket = null

// Initialisation au chargement du document
document.addEventListener("DOMContentLoaded", () => {
  console.log("🔧 Initialisation du monitoring...")

  // Vérifier que Chart.js est disponible
  if (typeof Chart === "undefined") {
    console.error("❌ Chart.js non disponible!")
    return
  }

  // Charger les données initiales
  loadInitialData()

  // Initialiser la connexion WebSocket
  initWebSocket()

  // Initialiser les graphiques
  initCharts()

  // Configurer les contrôles
  setupControls()

  // Configurer les boutons de toggle des graphiques
  setupChartToggles()

  console.log("✅ Monitoring initialisé")
})

/**
 * Charge les données initiales depuis les éléments script
 */
function loadInitialData() {
  console.log("📊 Chargement des données initiales...")

  // Charger les données initiales
  const dataElement = document.getElementById("initial-data")
  if (dataElement) {
    try {
      initialData = JSON.parse(dataElement.textContent)
      console.log("✅ Données initiales chargées:", Object.keys(initialData))
    } catch (error) {
      console.error("❌ Erreur lors du chargement des données initiales:", error)
      initialData = {}
    }
  } else {
    console.warn("⚠️ Élément initial-data non trouvé")
  }

  // Charger les seuils des capteurs
  const thresholdsElement = document.getElementById("sensor-thresholds")
  if (thresholdsElement) {
    try {
      sensorThresholds = JSON.parse(thresholdsElement.textContent)
      console.log("✅ Seuils chargés:", Object.keys(sensorThresholds))
    } catch (error) {
      console.error("❌ Erreur lors du chargement des seuils:", error)
      sensorThresholds = {}
    }
  } else {
    console.warn("⚠️ Élément sensor-thresholds non trouvé")
  }
}

/**
 * Initialise la connexion WebSocket
 */
function initWebSocket() {
  console.log("🔌 Connexion WebSocket...")

  try {
    socket = io()

    socket.on("connect", () => {
      console.log("✅ WebSocket connecté")
    })

    socket.on("disconnect", () => {
      console.log("❌ WebSocket déconnecté")
    })

    // Écouter les nouvelles données de capteurs
    socket.on("sensor_data", (data) => {
      console.log("📡 Données capteur reçues:", data.sensor_name, data.value)
      updateChart(data.sensor_name, data)
      updateDataTable(data)
    })

    socket.on("new_alert", (alert) => {
      console.log("🚨 Nouvelle alerte:", alert)
      showAlert(alert)
    })
  } catch (error) {
    console.error("❌ Erreur WebSocket:", error)
  }
}

/**
 * Initialise les graphiques pour tous les capteurs
 */
function initCharts() {
  console.log("📈 Initialisation des graphiques...")

  const sensorNames = [
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

  sensorNames.forEach((sensorName) => {
    initChart(sensorName)
  })

  console.log(`✅ ${Object.keys(charts).length} graphiques initialisés`)
}

/**
 * Initialise un graphique pour un capteur spécifique
 */
function initChart(sensorName) {
  const canvas = document.getElementById(`${sensorName}-chart`)
  if (!canvas) {
    console.warn(`⚠️ Canvas non trouvé pour ${sensorName}`)
    return
  }

  console.log(`📊 Création graphique pour ${sensorName}`)

  // Déterminer la couleur du graphique
  const color = getSensorColor(sensorName)

  // Créer le graphique
  const ctx = canvas.getContext("2d")
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
          tension: 0.3,
          fill: true,
          pointRadius: 2,
          pointBackgroundColor: color,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          mode: "index",
          intersect: false,
          callbacks: {
            label: (context) => {
              const unit = getUnitForSensor(sensorName)
              return `${context.dataset.label}: ${context.parsed.y} ${unit}`
            },
          },
        },
      },
      scales: {
        x: {
          type: "time",
          time: {
            unit: "minute",
            displayFormats: {
              minute: "HH:mm",
            },
          },
          title: {
            display: true,
            text: "Heure",
          },
        },
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: `${getSensorLabel(sensorName)} (${getUnitForSensor(sensorName)})`,
          },
        },
      },
    },
  })

  // Charger les données initiales si disponibles
  if (initialData[sensorName] && initialData[sensorName].length > 0) {
    console.log(`📊 Chargement données initiales pour ${sensorName}:`, initialData[sensorName].length, "points")
    updateChartWithData(sensorName, initialData[sensorName])
  } else {
    console.warn(`⚠️ Pas de données initiales pour ${sensorName}`)
    // Charger des données depuis l'API
    loadSensorData(sensorName, 24)
  }
}

/**
 * Charge les données d'un capteur depuis l'API
 */
function loadSensorData(sensorName, hours = 24) {
  console.log(`🔄 Chargement données API pour ${sensorName}`)

  fetch(`/api/sensor_data/${sensorName}?hours=${hours}`)
    .then((response) => response.json())
    .then((data) => {
      console.log(`✅ Données API reçues pour ${sensorName}:`, data.length, "points")
      if (data.length > 0) {
        updateChartWithData(sensorName, data)
      } else {
        console.warn(`⚠️ Aucune donnée API pour ${sensorName}`)
      }
    })
    .catch((error) => {
      console.error(`❌ Erreur chargement données ${sensorName}:`, error)
    })
}

/**
 * Met à jour un graphique avec de nouvelles données
 */
function updateChart(sensorName, data) {
  const chart = charts[sensorName]
  if (!chart) {
    console.warn(`⚠️ Graphique non trouvé pour ${sensorName}`)
    return
  }

  console.log(`📊 Mise à jour graphique ${sensorName}:`, data.value)

  // Ajouter la nouvelle donnée
  chart.data.labels.push(new Date(data.timestamp))
  chart.data.datasets[0].data.push(data.value)

  // Limiter à 100 points de données
  if (chart.data.labels.length > 100) {
    chart.data.labels.shift()
    chart.data.datasets[0].data.shift()
  }

  // Mettre à jour le graphique
  chart.update("none")
}

/**
 * Met à jour un graphique avec un ensemble de données
 */
function updateChartWithData(sensorName, dataArray) {
  const chart = charts[sensorName]
  if (!chart || !dataArray) {
    console.warn(`⚠️ Impossible de mettre à jour ${sensorName}`)
    return
  }

  console.log(`📊 Mise à jour complète ${sensorName}:`, dataArray.length, "points")

  // Convertir les données
  const labels = dataArray.map((item) => new Date(item.timestamp))
  const values = dataArray.map((item) => item.value)

  // Mettre à jour le graphique
  chart.data.labels = labels
  chart.data.datasets[0].data = values
  chart.update()
}

/**
 * Configure les contrôles de la page
 */
function setupControls() {
  console.log("⚙️ Configuration des contrôles...")

  // Contrôle de période
  const timeRangeSelect = document.getElementById("time-range")
  if (timeRangeSelect) {
    timeRangeSelect.addEventListener("change", function () {
      const hours = Number.parseInt(this.value)
      console.log(`🔄 Changement période: ${hours}h`)
      loadDataForAllSensors(hours)
    })
  }

  // Contrôle de rafraîchissement
  const refreshRateSelect = document.getElementById("refresh-rate")
  if (refreshRateSelect) {
    refreshRateSelect.addEventListener("change", function () {
      const rate = Number.parseInt(this.value)
      console.log(`🔄 Changement rafraîchissement: ${rate}s`)
      setupAutoRefresh(rate)
    })
  }

  // Bouton d'export
  const exportButton = document.getElementById("export-data")
  if (exportButton) {
    exportButton.addEventListener("click", exportAllData)
  }
}

/**
 * Configure le rafraîchissement automatique
 */
function setupAutoRefresh(intervalSeconds) {
  // Arrêter l'intervalle précédent
  if (window.refreshInterval) {
    clearInterval(window.refreshInterval)
  }

  // Démarrer un nouveau rafraîchissement si nécessaire
  if (intervalSeconds > 0) {
    console.log(`⏰ Rafraîchissement auto: ${intervalSeconds}s`)
    window.refreshInterval = setInterval(() => {
      const timeRange = document.getElementById("time-range")
      const hours = timeRange ? Number.parseInt(timeRange.value) : 24
      loadDataForAllSensors(hours)
    }, intervalSeconds * 1000)
  }
}

/**
 * Charge les données pour tous les capteurs
 */
function loadDataForAllSensors(hours) {
  console.log(`🔄 Rechargement toutes données: ${hours}h`)
  const sensorNames = Object.keys(charts)

  sensorNames.forEach((sensorName) => {
    loadSensorData(sensorName, hours)
  })
}

/**
 * Configure les boutons de toggle des graphiques
 */
function setupChartToggles() {
  const toggleButtons = document.querySelectorAll(".toggle-chart-btn")

  toggleButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const target = this.getAttribute("data-target")
      const targetElement = document.getElementById(target)
      const icon = this.querySelector("i")

      if (targetElement) {
        if (targetElement.style.display === "none") {
          targetElement.style.display = "block"
          icon.className = "fas fa-chevron-up"
        } else {
          targetElement.style.display = "none"
          icon.className = "fas fa-chevron-down"
        }
      }
    })
  })
}

/**
 * Met à jour le tableau de données
 */
function updateDataTable(data) {
  const tableBody = document.getElementById("data-table-body")
  if (!tableBody) return

  // Créer une nouvelle ligne
  const row = document.createElement("tr")
  row.innerHTML = `
        <td>${formatDate(data.timestamp)}</td>
        <td>${getSensorLabel(data.sensor_name)}</td>
        <td>${data.value}</td>
        <td>${data.unit}</td>
    `

  // Ajouter la ligne au début du tableau
  tableBody.insertBefore(row, tableBody.firstChild)

  // Limiter à 100 lignes
  while (tableBody.children.length > 100) {
    tableBody.removeChild(tableBody.lastChild)
  }
}

/**
 * Affiche une alerte
 */
function showAlert(alert) {
  // Créer une notification
  const notification = document.createElement("div")
  notification.className = "alert alert-warning alert-dismissible fade show"
  notification.innerHTML = `
        <strong>Nouvelle alerte!</strong> ${alert.message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `

  // Ajouter au container d'alertes
  const alertContainer = document.getElementById("alert-container")
  if (alertContainer) {
    alertContainer.appendChild(notification)

    // Supprimer après 5 secondes
    setTimeout(() => {
      notification.remove()
    }, 5000)
  }
}

/**
 * Exporte toutes les données
 */
function exportAllData() {
  console.log("📤 Export des données...")
  const timeRange = document.getElementById("time-range")
  const hours = timeRange ? Number.parseInt(timeRange.value) : 24
  const sensorNames = Object.keys(charts)

  // Collecter toutes les données
  const allData = []
  let completedRequests = 0

  sensorNames.forEach((sensorName) => {
    fetch(`/api/sensor_data/${sensorName}?hours=${hours}`)
      .then((response) => response.json())
      .then((data) => {
        data.forEach((item) => {
          allData.push({
            timestamp: item.timestamp,
            sensor: getSensorLabel(sensorName),
            value: item.value,
            unit: item.unit,
          })
        })

        completedRequests++
        if (completedRequests === sensorNames.length) {
          // Trier par timestamp
          allData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))

          // Exporter au format CSV
          const filename = `donnees_capteurs_${new Date().toISOString().split("T")[0]}.csv`
          exportToCSV(allData, filename)
        }
      })
      .catch((error) => {
        console.error(`❌ Erreur export ${sensorName}:`, error)
        completedRequests++
      })
  })
}

/**
 * Exporte les données au format CSV
 */
function exportToCSV(data, filename) {
  const csvRows = []
  const headers = Object.keys(data[0])
  csvRows.push(headers.join(","))

  for (const row of data) {
    const values = headers.map((header) => {
      const escaped = ("" + row[header]).replace(/"/g, '""')
      return `"${escaped}"`
    })
    csvRows.push(values.join(","))
  }

  const csvData = csvRows.join("\n")

  const blob = new Blob([csvData], { type: "text/csv" })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.setAttribute("hidden", "")
  a.setAttribute("href", url)
  a.setAttribute("download", filename)
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)

  console.log(`✅ Export terminé: ${filename}`)
}

/**
 * Retourne la couleur d'un capteur
 */
function getSensorColor(sensorName) {
  const colors = {
    nitrogen: "#3498db",
    phosphorus: "#2ecc71",
    potassium: "#e74c3c",
    ph: "#9b59b6",
    conductivity: "#f39c12",
    temperature: "#e67e22",
    humidity: "#1abc9c",
    salinity: "#34495e",
    water_level: "#3498db",
    water_temperature: "#e67e22",
    water_flow: "#2ecc71",
    water_pressure: "#9b59b6",
  }
  return colors[sensorName] || "#3498db"
}

/**
 * Retourne le libellé d'un capteur
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

/**
 * Retourne l'unité d'un capteur
 */
function getUnitForSensor(sensorName) {
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

/**
 * Formate une date pour l'affichage
 */
function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleString("fr-FR")
}

// Vérification de Chart.js au chargement
if (typeof Chart !== "undefined") {
  console.log("✅ Chart.js disponible")
} else {
  console.error("❌ Chart.js non trouvé!")
}
