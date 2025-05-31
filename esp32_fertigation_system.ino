// Système d'Irrigation Automatique pour Culture de Riz
// Version adaptée pour communication HTTP avec l'application Flask

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <HardwareSerial.h>

// ######################### CONFIGURATION HARDWARE #########################
// Communication série
HardwareSerial mySerial(2);  // UART2 : RX sur GPIO16, TX sur GPIO17
#define DEBUG_SERIAL Serial  // Pour les sorties de débogage

// Broches actionneurs
#define PUMP_RELAY_PIN 18    // Commande de la pompe via relais
#define BUZZER_PIN 19        // Buzzer pour alarme
#define FLOAT_SENSOR_PIN 34  // Capteur de niveau flottant (entrée analogique)
#define FLOW_SENSOR_PIN 21   // Débitmètre (interruption)

// ######################### CONFIGURATION RÉSEAU #########################
// IMPORTANT: Modifiez ces paramètres selon votre réseau
const char* ssid = "VotreWiFi";           // Nom de votre réseau WiFi
const char* password = "VotreMotDePasse"; // Mot de passe WiFi
const char* serverURL = "http://192.168.1.100:5000/api/sensor_data"; // IP de votre serveur Flask

// ######################### CONSTANTES SYSTEME #########################
// Seuils NPK pour la culture du riz (stade germination/semis)
#define NPK_CRITICAL_N 20    // Azote critique < 20 mg/kg
#define NPK_CRITICAL_P 10    // Phosphore critique < 10 mg/kg  
#define NPK_CRITICAL_K 50    // Potassium critique < 50 mg/kg
#define NPK_OPTIMAL_N 30     // Azote optimal >= 30 mg/kg
#define NPK_OPTIMAL_P 15     // Phosphore optimal >= 15 mg/kg
#define NPK_OPTIMAL_K 60     // Potassium optimal >= 60 mg/kg

// Paramètres système
#define PUMP_RUN_TIME 30000    // Durée max pompage (ms)
#define FLOW_CALIBRATION_FACTOR 4.5 // Pulses par litre
#define PRESSURE_CONSTANT 0.433     // Constante pression
#define WATER_LEVEL_THRESHOLD 2000  // Seuil capteur flottant

// Intervalles de communication
#define SENSOR_READ_INTERVAL 5000    // Lecture capteurs toutes les 5s
#define HTTP_SEND_INTERVAL 10000     // Envoi HTTP toutes les 10s
#define DISPLAY_INTERVAL 15000       // Affichage toutes les 15s

// ######################### VARIABLES GLOBALES #########################
// Données capteur de sol NPK 8-en-1
unsigned int soilTemperature, soilConductivity, soilPH, nitrogen, phosphorus, potassium, soilHumidity, salinity;

// Variables système
volatile uint16_t flowPulseCount = 0;
float flowRate = 0.0;
float totalVolume = 0.0;
float pressure = 0.0;
bool pumpStatus = false;
bool alarmStatus = false;
bool waterLevelLow = false;
int sensorValue = 0;

// Timers
unsigned long lastPumpTime = 0;
unsigned long lastFlowCalc = 0;
unsigned long lastSensorRead = 0;
unsigned long lastHTTPSend = 0;
unsigned long lastDisplayTime = 0;
unsigned long lastWaterLevelCheck = 0;

// Variables de connexion
bool wifiConnected = false;
int httpFailureCount = 0;
const int MAX_HTTP_FAILURES = 5;

// ######################### FONCTIONS CAPTEUR SOL #########################
bool readSensorData() {
  byte queryData[] = {0x01, 0x03, 0x00, 0x00, 0x00, 0x07, 0x04, 0x08};
  byte receivedData[19];
  
  // Vider le buffer de réception
  while (mySerial.available()) {
    mySerial.read();
  }
  
  // Envoyer la requête
  mySerial.write(queryData, sizeof(queryData));
  delay(100);  // Attendre la réponse
  
  // Vérifier si des données sont disponibles
  if (mySerial.available() >= sizeof(receivedData)) {
    mySerial.readBytes(receivedData, sizeof(receivedData));
    
    // Extraire les données
    soilHumidity     = (receivedData[3]  << 8) | receivedData[4];
    soilTemperature  = (receivedData[5]  << 8) | receivedData[6];
    soilConductivity = (receivedData[7]  << 8) | receivedData[8];
    soilPH           = (receivedData[9]  << 8) | receivedData[10];
    nitrogen         = (receivedData[11] << 8) | receivedData[12];
    phosphorus       = (receivedData[13] << 8) | receivedData[14];
    potassium        = (receivedData[15] << 8) | receivedData[16];
    
    // Calculer la salinité (approximation basée sur la conductivité)
    salinity = soilConductivity * 0.64; // Conversion approximative µS/cm vers ppm
    
    DEBUG_SERIAL.println("✓ Lecture capteur sol réussie");
    return true;
  } else {
    DEBUG_SERIAL.println("✗ Erreur lecture capteur sol - Pas assez de données");
    return false;
  }
}

// ######################### FONCTIONS DÉBITMÈTRE #########################
void IRAM_ATTR flowPulseCounter() {
  flowPulseCount++;
}

void calculateFlowRate() {
  detachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN));
  
  float deltaTime = (millis() - lastFlowCalc) / 1000.0; // en secondes
  if (deltaTime > 0) {
    flowRate = (flowPulseCount / deltaTime) / (FLOW_CALIBRATION_FACTOR * 60.0);
    totalVolume += flowPulseCount / (FLOW_CALIBRATION_FACTOR * 60.0);
    pressure = sq(flowRate) * PRESSURE_CONSTANT;
  }
  
  flowPulseCount = 0;
  lastFlowCalc = millis();
  attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN), flowPulseCounter, FALLING);
}

// ######################### FONCTIONS CONTRÔLE #########################
void controlPump() {
  // Vérification des seuils critiques NPK
  bool nitrogenCritical = (nitrogen < NPK_CRITICAL_N);
  bool phosphorusCritical = (phosphorus < NPK_CRITICAL_P);
  bool potassiumCritical = (potassium < NPK_CRITICAL_K);
  
  // Vérification des seuils optimaux NPK
  bool nitrogenOptimal = (nitrogen >= NPK_OPTIMAL_N);
  bool phosphorusOptimal = (phosphorus >= NPK_OPTIMAL_P);
  bool potassiumOptimal = (potassium >= NPK_OPTIMAL_K);
  
  // Activation de la pompe si TOUS les éléments NPK sont en dessous des seuils critiques
  if (nitrogenCritical && phosphorusCritical && potassiumCritical && !pumpStatus) {
    if (checkWaterLevel()) {
      digitalWrite(PUMP_RELAY_PIN, HIGH);
      pumpStatus = true;
      lastPumpTime = millis();
      DEBUG_SERIAL.println("🚨 Pompe activée - NPK critique:");
      DEBUG_SERIAL.printf("  N: %d mg/kg (< %d)\n", nitrogen, NPK_CRITICAL_N);
      DEBUG_SERIAL.printf("  P: %d mg/kg (< %d)\n", phosphorus, NPK_CRITICAL_P);
      DEBUG_SERIAL.printf("  K: %d mg/kg (< %d)\n", potassium, NPK_CRITICAL_K);
    }
  } 
  // Arrêt de la pompe si TOUS les éléments NPK atteignent les seuils optimaux OU timeout
  else if ((nitrogenOptimal && phosphorusOptimal && potassiumOptimal) || 
           (pumpStatus && (millis() - lastPumpTime > PUMP_RUN_TIME))) {
    digitalWrite(PUMP_RELAY_PIN, LOW);
    pumpStatus = false;
    
    if (nitrogenOptimal && phosphorusOptimal && potassiumOptimal) {
      DEBUG_SERIAL.println("✅ Pompe désactivée - NPK optimal atteint:");
      DEBUG_SERIAL.printf("  N: %d mg/kg (>= %d)\n", nitrogen, NPK_OPTIMAL_N);
      DEBUG_SERIAL.printf("  P: %d mg/kg (>= %d)\n", phosphorus, NPK_OPTIMAL_P);
      DEBUG_SERIAL.printf("  K: %d mg/kg (>= %d)\n", potassium, NPK_OPTIMAL_K);
    } else {
      DEBUG_SERIAL.println("⏰ Pompe désactivée - Temps maximum atteint");
    }
  }
}

bool checkWaterLevel() {
  // Lecture périodique pour éviter les lectures trop fréquentes
  if (millis() - lastWaterLevelCheck > 1000) {
    sensorValue = analogRead(FLOAT_SENSOR_PIN);
    lastWaterLevelCheck = millis();
  }
  
  if (sensorValue < WATER_LEVEL_THRESHOLD) {
    if (!alarmStatus) {
      DEBUG_SERIAL.println("🚨 ALARME: Réservoir vide!");
      alarmStatus = true;
      waterLevelLow = true;
      // Activer le buzzer
      tone(BUZZER_PIN, 1000, 500);
    }
    return false;
  }
  
  alarmStatus = false;
  waterLevelLow = false;
  noTone(BUZZER_PIN);
  return true;
}

// ######################### COMMUNICATION HTTP #########################
bool sendDataToServer() {
  if (!wifiConnected) {
    DEBUG_SERIAL.println("❌ WiFi non connecté - Impossible d'envoyer les données");
    return false;
  }
  
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  // Créer le JSON pour le capteur NPK 8-en-1
  DynamicJsonDocument npkDoc(1024);
  npkDoc["sensor_type"] = "npk_8in1";
  npkDoc["nitrogen"] = nitrogen;
  npkDoc["phosphorus"] = phosphorus;
  npkDoc["potassium"] = potassium;
  npkDoc["ph"] = soilPH / 10.0;  // Conversion en valeur décimale
  npkDoc["conductivity"] = soilConductivity;
  npkDoc["temperature"] = soilTemperature / 10.0;  // Conversion en valeur décimale
  npkDoc["humidity"] = soilHumidity / 10.0;  // Conversion en valeur décimale
  npkDoc["salinity"] = salinity;
  npkDoc["timestamp"] = millis();
  
  String npkPayload;
  serializeJson(npkDoc, npkPayload);
  
  DEBUG_SERIAL.println("📡 Envoi données NPK: " + npkPayload);
  
  int httpResponseCode = http.POST(npkPayload);
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    DEBUG_SERIAL.println("✅ Données NPK envoyées avec succès");
    DEBUG_SERIAL.println("Réponse serveur: " + response);
    httpFailureCount = 0;
  } else {
    DEBUG_SERIAL.printf("❌ Erreur HTTP NPK: %d\n", httpResponseCode);
    httpFailureCount++;
  }
  
  http.end();
  
  // Envoyer les données de niveau d'eau
  delay(1000); // Petite pause entre les envois
  
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  DynamicJsonDocument waterDoc(512);
  waterDoc["sensor_type"] = "water_level";
  waterDoc["level"] = map(sensorValue, 0, 4095, 0, 100); // Conversion en pourcentage
  waterDoc["temperature"] = soilTemperature / 10.0; // Utiliser la température du sol
  waterDoc["timestamp"] = millis();
  
  String waterPayload;
  serializeJson(waterDoc, waterPayload);
  
  DEBUG_SERIAL.println("📡 Envoi données niveau d'eau: " + waterPayload);
  
  httpResponseCode = http.POST(waterPayload);
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    DEBUG_SERIAL.println("✅ Données niveau d'eau envoyées avec succès");
  } else {
    DEBUG_SERIAL.printf("❌ Erreur HTTP niveau d'eau: %d\n", httpResponseCode);
    httpFailureCount++;
  }
  
  http.end();
  
  // Envoyer les données de débit d'eau
  delay(1000); // Petite pause entre les envois
  
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  DynamicJsonDocument flowDoc(512);
  flowDoc["sensor_type"] = "water_flow";
  flowDoc["flow"] = flowRate;
  flowDoc["pressure"] = pressure;
  flowDoc["timestamp"] = millis();
  
  String flowPayload;
  serializeJson(flowDoc, flowPayload);
  
  DEBUG_SERIAL.println("📡 Envoi données débit: " + flowPayload);
  
  httpResponseCode = http.POST(flowPayload);
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    DEBUG_SERIAL.println("✅ Données débit envoyées avec succès");
    return true;
  } else {
    DEBUG_SERIAL.printf("❌ Erreur HTTP débit: %d\n", httpResponseCode);
    httpFailureCount++;
    return false;
  }
  
  http.end();
}

// ######################### FONCTIONS WIFI #########################
bool connectToWiFi() {
  DEBUG_SERIAL.print("🔗 Connexion au WiFi: ");
  DEBUG_SERIAL.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    DEBUG_SERIAL.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    DEBUG_SERIAL.println();
    DEBUG_SERIAL.print("✅ WiFi connecté! IP: ");
    DEBUG_SERIAL.println(WiFi.localIP());
    DEBUG_SERIAL.print("🎯 Serveur cible: ");
    DEBUG_SERIAL.println(serverURL);
    wifiConnected = true;
    return true;
  } else {
    DEBUG_SERIAL.println();
    DEBUG_SERIAL.println("❌ Échec connexion WiFi");
    wifiConnected = false;
    return false;
  }
}

void checkWiFiConnection() {
  if (WiFi.status() != WL_CONNECTED) {
    wifiConnected = false;
    DEBUG_SERIAL.println("📶 Connexion WiFi perdue - Tentative de reconnexion...");
    connectToWiFi();
  }
}

// ######################### AFFICHAGE #########################
void displaySystemStatus() {
  DEBUG_SERIAL.println("\n========== SYSTÈME FERTIGATION ESP32 ==========");
  
  // État de la connexion
  DEBUG_SERIAL.printf("📶 WiFi: %s", wifiConnected ? "Connecté" : "Déconnecté");
  if (wifiConnected) {
    DEBUG_SERIAL.printf(" (IP: %s)", WiFi.localIP().toString().c_str());
  }
  DEBUG_SERIAL.println();
  DEBUG_SERIAL.printf("📡 Serveur: %s\n", serverURL);
  DEBUG_SERIAL.printf("❌ Échecs HTTP: %d/%d\n", httpFailureCount, MAX_HTTP_FAILURES);
  
  // Données capteurs
  DEBUG_SERIAL.println("\n--- CAPTEUR NPK 8-EN-1 ---");
  DEBUG_SERIAL.printf("🌡️  Température: %.1f°C\n", soilTemperature/10.0);
  DEBUG_SERIAL.printf("💧 Humidité: %.1f%%\n", soilHumidity/10.0);
  DEBUG_SERIAL.printf("⚡ Conductivité: %d µS/cm\n", soilConductivity);
  DEBUG_SERIAL.printf("🧪 pH: %.1f\n", soilPH/10.0);
  DEBUG_SERIAL.printf("🧬 Salinité: %d ppm\n", salinity);
  DEBUG_SERIAL.printf("🍃 N: %d mg/kg %s\n", nitrogen, 
                     (nitrogen < NPK_CRITICAL_N) ? "(CRITIQUE)" : 
                     (nitrogen >= NPK_OPTIMAL_N) ? "(OPTIMAL)" : "(MOYEN)");
  DEBUG_SERIAL.printf("🔥 P: %d mg/kg %s\n", phosphorus,
                     (phosphorus < NPK_CRITICAL_P) ? "(CRITIQUE)" : 
                     (phosphorus >= NPK_OPTIMAL_P) ? "(OPTIMAL)" : "(MOYEN)");
  DEBUG_SERIAL.printf("🌿 K: %d mg/kg %s\n", potassium,
                     (potassium < NPK_CRITICAL_K) ? "(CRITIQUE)" : 
                     (potassium >= NPK_OPTIMAL_K) ? "(OPTIMAL)" : "(MOYEN)");
  
  // État du système
  DEBUG_SERIAL.println("\n--- SYSTÈME IRRIGATION ---");
  DEBUG_SERIAL.printf("💧 Pompe: %s\n", pumpStatus ? "🟢 ACTIVE" : "🔴 ARRÊTÉE");
  DEBUG_SERIAL.printf("🪣 Réservoir: %s (valeur: %d)\n", 
                     waterLevelLow ? "🔴 VIDE" : "🟢 OK", sensorValue);
  DEBUG_SERIAL.printf("🌊 Débit: %.2f L/min\n", flowRate);
  DEBUG_SERIAL.printf("📊 Pression: %.2f psi\n", pressure);
  DEBUG_SERIAL.printf("📈 Volume total: %.2f L\n", totalVolume);
  DEBUG_SERIAL.printf("🚨 Alarme: %s\n", alarmStatus ? "🔴 ACTIVE" : "🟢 INACTIVE");
  
  DEBUG_SERIAL.println("===============================================\n");
}

// ######################### FONCTION SETUP #########################
void setup() {
  // Initialisation série
  DEBUG_SERIAL.begin(115200);
  mySerial.begin(9600, SERIAL_8N1, 16, 17);
  
  DEBUG_SERIAL.println("\n🌱 ========================================");
  DEBUG_SERIAL.println("🌾 SYSTÈME FERTIGATION ESP32 - CULTURE DE RIZ");
  DEBUG_SERIAL.println("📡 Version HTTP pour application Flask");
  DEBUG_SERIAL.println("🌱 ========================================");
  
  // Configuration des broches
  pinMode(PUMP_RELAY_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(FLOAT_SENSOR_PIN, INPUT);
  pinMode(FLOW_SENSOR_PIN, INPUT_PULLUP);
  
  // État initial
  digitalWrite(PUMP_RELAY_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  
  // Configuration interruption débitmètre
  attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN), flowPulseCounter, FALLING);
  
  // Initialisation des timers
  lastSensorRead = millis();
  lastHTTPSend = millis();
  lastDisplayTime = millis();
  lastFlowCalc = millis();
  lastWaterLevelCheck = millis();
  
  // Configuration WiFi
  WiFi.mode(WIFI_STA);
  connectToWiFi();
  
  DEBUG_SERIAL.println("✅ Système initialisé avec succès!");
  DEBUG_SERIAL.println("🚀 Démarrage de la boucle principale...\n");
}

// ######################### FONCTION LOOP PRINCIPALE #########################
void loop() {
  unsigned long currentTime = millis();
  
  // Vérification connexion WiFi
  if (currentTime % 30000 == 0) { // Vérifier toutes les 30 secondes
    checkWiFiConnection();
  }
  
  // Lecture des capteurs du sol
  if (currentTime - lastSensorRead >= SENSOR_READ_INTERVAL) {
    if (readSensorData()) {
      DEBUG_SERIAL.println("✓ Lecture capteurs réussie");
    } else {
      DEBUG_SERIAL.println("✗ Erreur lecture capteurs");
    }
    lastSensorRead = currentTime;
  }
  
  // Calcul du débit
  if (currentTime - lastFlowCalc >= 1000) {
    calculateFlowRate();
  }
  
  // Contrôle de l'irrigation
  controlPump();
  
  // Vérification niveau d'eau
  checkWaterLevel();
  
  // Envoi des données via HTTP
  if (currentTime - lastHTTPSend >= HTTP_SEND_INTERVAL) {
    if (wifiConnected) {
      if (sendDataToServer()) {
        DEBUG_SERIAL.println("📤 Cycle d'envoi HTTP terminé avec succès");
      } else {
        DEBUG_SERIAL.println("📤 Échec du cycle d'envoi HTTP");
      }
      
      // Si trop d'échecs, tenter de reconnecter
      if (httpFailureCount >= MAX_HTTP_FAILURES) {
        DEBUG_SERIAL.println("🔄 Trop d'échecs HTTP - Reconnexion WiFi...");
        connectToWiFi();
        httpFailureCount = 0;
      }
    } else {
      DEBUG_SERIAL.println("📤 Envoi HTTP ignoré - WiFi non connecté");
    }
    lastHTTPSend = currentTime;
  }
  
  // Affichage périodique du statut
  if (currentTime - lastDisplayTime >= DISPLAY_INTERVAL) {
    displaySystemStatus();
    lastDisplayTime = currentTime;
  }
  
  // Petite pause pour éviter la surcharge du processeur
  delay(100);
}