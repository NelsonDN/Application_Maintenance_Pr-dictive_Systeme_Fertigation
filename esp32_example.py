"""
Code d'exemple pour ESP32 - Communication HTTP simple
Ce code montre comment l'ESP32 doit envoyer les données
"""
import urequests
import ujson
import time
from machine import Pin, ADC, I2C
import network

# Configuration WiFi
WIFI_SSID = "VotreWiFi"
WIFI_PASSWORD = "VotreMotDePasse"

# Configuration serveur
SERVER_URL = "http://192.168.1.100:5000/api/sensor_data"  # Remplacez par l'IP de votre serveur

# Configuration des capteurs (exemple)
# Adaptez selon vos capteurs réels
class SensorReader:
    def __init__(self):
        # Initialiser vos capteurs ici
        # Exemple pour des capteurs analogiques
        self.adc_nitrogen = ADC(Pin(34))
        self.adc_phosphorus = ADC(Pin(35))
        # ... autres capteurs
        
    def read_npk_sensor(self):
        """Lit les données du capteur NPK 8-en-1"""
        # Remplacez par la lecture réelle de vos capteurs
        # Ceci est un exemple avec des valeurs simulées
        
        # Lecture des valeurs analogiques et conversion
        nitrogen_raw = self.adc_nitrogen.read()
        phosphorus_raw = self.adc_phosphorus.read()
        
        # Conversion en valeurs réelles (à adapter selon vos capteurs)
        nitrogen = (nitrogen_raw / 4095.0) * 1000  # Exemple de conversion
        phosphorus = (phosphorus_raw / 4095.0) * 500
        
        # Pour cet exemple, on simule les autres valeurs
        # Dans la réalité, vous lirez tous vos capteurs
        data = {
            'sensor_type': 'npk_8in1',
            'nitrogen': nitrogen,
            'phosphorus': phosphorus,
            'potassium': 520.0,  # À remplacer par lecture réelle
            'ph': 7.2,
            'conductivity': 1200.0,
            'temperature': 25.0,
            'humidity': 65.0,
            'salinity': 800.0,
            'timestamp': time.time()
        }
        
        return data
    
    def read_water_level_sensor(self):
        """Lit les données du capteur de niveau d'eau"""
        # Exemple de lecture - à adapter selon votre capteur
        data = {
            'sensor_type': 'water_level',
            'level': 75.0,  # Pourcentage
            'temperature': 24.0,  # Température de l'eau
            'timestamp': time.time()
        }
        
        return data
    
    def read_water_flow_sensor(self):
        """Lit les données du capteur de débit d'eau"""
        # Exemple de lecture - à adapter selon votre capteur
        data = {
            'sensor_type': 'water_flow',
            'flow': 5.5,  # L/min
            'pressure': 1.8,  # bar
            'timestamp': time.time()
        }
        
        return data

def connect_wifi():
    """Connexion au WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connexion au WiFi...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # Attendre la connexion
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
        
        if wlan.isconnected():
            print('WiFi connecté:', wlan.ifconfig())
            return True
        else:
            print('Échec de connexion WiFi')
            return False
    
    return True

def send_data(data):
    """Envoie les données au serveur via HTTP POST"""
    try:
        headers = {'Content-Type': 'application/json'}
        response = urequests.post(
            SERVER_URL,
            data=ujson.dumps(data),
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ Données envoyées: {data['sensor_type']}")
            response_data = response.json()
            print(f"Réponse serveur: {response_data}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
        
        response.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi: {e}")
        return False

def main():
    """Fonction principale"""
    print("🌱 ESP32 - Système de maintenance prédictive")
    print("📡 Communication HTTP avec le serveur")
    
    # Connexion WiFi
    if not connect_wifi():
        print("❌ Impossible de se connecter au WiFi")
        return
    
    # Initialiser les capteurs
    sensors = SensorReader()
    
    print("🔄 Démarrage de l'envoi des données...")
    
    cycle = 0
    while True:
        try:
            cycle += 1
            print(f"\n📊 Cycle {cycle}")
            
            # Lire et envoyer les données NPK
            npk_data = sensors.read_npk_sensor()
            send_data(npk_data)
            
            time.sleep(3)
            
            # Lire et envoyer les données de niveau d'eau
            water_level_data = sensors.read_water_level_sensor()
            send_data(water_level_data)
            
            time.sleep(3)
            
            # Lire et envoyer les données de débit d'eau
            water_flow_data = sensors.read_water_flow_sensor()
            send_data(water_flow_data)
            
            # Attendre avant le prochain cycle
            print("⏳ Attente 4 secondes...")
            time.sleep(4)  # Total: 10 secondes par cycle
            
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé")
            break
        except Exception as e:
            print(f"❌ Erreur dans la boucle principale: {e}")
            time.sleep(5)

# Démarrer le programme
if __name__ == '__main__':
    main()
