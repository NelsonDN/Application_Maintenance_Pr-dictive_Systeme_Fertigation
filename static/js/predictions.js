/**
 * Script pour la page des prédictions
 */

document.addEventListener("DOMContentLoaded", () => {
  initializePredictions()
  setupEventListeners()
})

/**
 * Initialise la page des prédictions
 */
function initializePredictions() {
  console.log("🔮 Initialisation de la page des prédictions")
}

/**
 * Configure les écouteurs d'événements
 */
function setupEventListeners() {
  // Bouton de forçage de l'analyse
  const forceAnalysisBtn = document.getElementById("force-analysis-btn")
  if (forceAnalysisBtn) {
    forceAnalysisBtn.addEventListener("click", forceAnalysis)
  }

  // Bouton d'actualisation
  const refreshBtn = document.getElementById("refresh-predictions-btn")
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      location.reload()
    })
  }
}

/**
 * Force l'analyse prédictive
 */
function forceAnalysis() {
  const button = document.getElementById("force-analysis-btn")
  const originalText = button.innerHTML

  // Désactiver le bouton et afficher le chargement
  button.disabled = true
  button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyse en cours...'

  fetch("/api/force_predictive_analysis", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Afficher une notification de succès
        if (window.MainApp && window.MainApp.showNotification) {
          window.MainApp.showNotification("Analyse terminée", data.message, "success")
        }

        // Actualiser la page après 2 secondes
        setTimeout(() => {
          location.reload()
        }, 2000)
      } else {
        throw new Error(data.error || "Erreur lors de l'analyse")
      }
    })
    .catch((error) => {
      console.error("❌ Erreur lors de l'analyse prédictive:", error)

      // Restaurer le bouton
      button.disabled = false
      button.innerHTML = originalText

      // Afficher une notification d'erreur
      if (window.MainApp && window.MainApp.showNotification) {
        window.MainApp.showNotification("Erreur", "Impossible d'effectuer l'analyse", "danger")
      } else {
        alert("Erreur lors de l'analyse prédictive")
      }
    })
}

// Exporter pour utilisation globale
window.PredictionsApp = {
  forceAnalysis,
}
