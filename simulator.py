"""
Simulateur de données pour les capteurs ESP32
"""
import time
import json
import random
import threading
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
from config import Config

class ESP32Simulator:
    def __init__(self):
        self.client = mqtt.Client(client_id="esp32_simulator")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
        self.running = False
        self.thread = None
        
        # État initial des capteurs
        self.sensor_states = {
            # Capteur NPK 8-en-1
            'nitrogen': {'value': 450.0, 'trend': 0.0, 'noise_level': 15.0},
            'phosphorus': {'value': 280.0, 'trend': 0.0, 'noise_level': 12.0},
            'potassium': {'value': 520.0, 'trend': 0.0, 'noise_level': 18.0},
            'ph': {'value': 7.2, 'trend': 0.0, 'noise_level': 0.1},
            'conductivity': {'value': 1200.0, 'trend': 0.0, 'noise_level': 50.0},
            'temperature': {'value': 25.0, 'trend': 0.0, 'noise_level': 1.5},
            'humidity': {'value': 65.0, 'trend': 0.0, 'noise_level': 3.0},
            'salinity': {'value': 800.0, 'trend': 0.0, 'noise_level': 30.0},
            
            # Capteur niveau d'eau
            'water_level': {'value': 75.0, 'trend': 0.0, 'noise_level': 2.0},
            'water_temperature': {'value': 24.0, 'trend': 0.0, 'noise_level': 1.0},
            
            # Capteur débit d'eau
            'water_flow': {'value': 5.5, 'trend': 0.0, 'noise_level': 0.3},
            'water_pressure': {'value': 1.8, 'trend': 0.0, 'noise_level': 0.1}
        }
        
        # État du système
        self.system_state = {
            'uptime': 0,
            'battery': 100.0,
            'wifi_strength': -65,
            'errors': []
        }
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback lors de la connexion au broker MQTT"""
        if rc == 0:
            print("ESP32 Simulator: Connecté au broker MQTT")
            # S'abonner aux topics de commande
            client.subscribe("esp32/command/#")
            client.message_callback_add("esp32/command/#", self.on_command)
        else:
            print(f"ESP32 Simulator: Échec de connexion au broker MQTT, code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback lors de la déconnexion du broker MQTT"""
        print("ESP32 Simulator: Déconnecté du broker MQTT")
    
    def on_command(self, client, userdata, msg):
        """Traitement des commandes reçues"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            print(f"ESP32 Simulator: Commande reçue sur {topic}: {payload}")
            
            # Traiter les différentes commandes
            if topic == "esp32/command/reset":
                print("ESP32 Simulator: Simulation de redémarrage")
                self.system_state['uptime'] = 0
                self.system_state['errors'] = []
            
            elif topic == "esp32/command/calibrate":
                sensor = payload.get('sensor')
                if sensor in self.sensor_states:
                    print(f"ESP32 Simulator: Calibration du capteur {sensor}")
                    # Réinitialiser la tendance
                    self.sensor_states[sensor]['trend'] = 0.0
            
            # Envoyer un accusé de réception
            self.client.publish("esp32/system/ack", json.dumps({
                'command': topic,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }))
            
        except Exception as e:
            print(f"ESP32 Simulator: Erreur lors du traitement de la commande: {e}")
    
    def connect(self):
        """Connexion au broker MQTT"""
        try:
            self.client.connect(
                Config.MQTT_BROKER_HOST,
                Config.MQTT_BROKER_PORT,
                Config.MQTT_KEEPALIVE
            )
            self.client.loop_start()
            print(f"ESP32 Simulator: Tentative de connexion à {Config.MQTT_BROKER_HOST}:{Config.MQTT_BROKER_PORT}")
            return True
        except Exception as e:
            print(f"ESP32 Simulator: Erreur de connexion: {e}")
            return False
    
    def disconnect(self):
        """Déconnexion du broker MQTT"""
        self.running = False
        if self.thread:
            self.thread.join()
        
        self.client.loop_stop()
        self.client.disconnect()
        print("ESP32 Simulator: Déconnecté")
    
    def start(self):
        """Démarrage de la simulation"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._simulation_loop)
        self.thread.daemon = True
        self.thread.start()
        print("ESP32 Simulator: Simulation démarrée")
    
    def _simulation_loop(self):
        """Boucle principale de simulation"""
        while self.running:
            try:
                # Simuler les données NPK 8-en-1
                npk_data = self._generate_npk_data()
                self.client.publish(Config.MQTT_TOPICS['npk_sensor'], json.dumps(npk_data))
                
                time.sleep(2)  # Attendre 2 secondes
                
                # Simuler les données de niveau d'eau
                water_level_data = self._generate_water_level_data()
                self.client.publish(Config.MQTT_TOPICS['water_level'], json.dumps(water_level_data))
                
                time.sleep(2)  # Attendre 2 secondes
                
                # Simuler les données de débit d'eau
                water_flow_data = self._generate_water_flow_data()
                self.client.publish(Config.MQTT_TOPICS['water_flow'], json.dumps(water_flow_data))
                
                # Mettre à jour l'état du système
                self._update_system_state()
                self.client.publish(Config.MQTT_TOPICS['system_status'], json.dumps(self.system_state))
                
                time.sleep(6)  # Attendre 6 secondes (total 10 secondes par cycle)
                
            except Exception as e:
                print(f"ESP32 Simulator: Erreur dans la simulation: {e}")
                time.sleep(5)
    
    def _generate_npk_data(self):
        """Génère des données simulées pour le capteur NPK 8-en-1"""
        data = {}
        
        # Simuler chaque paramètre du capteur NPK
        for sensor_name in ['nitrogen', 'phosphorus', 'potassium', 'ph', 'conductivity', 'temperature', 'humidity', 'salinity']:
            state = self.sensor_states[sensor_name]
            
            # Ajouter une tendance lente (dérive)
            state['trend'] += random.uniform(-0.01, 0.01)
            state['trend'] = max(-0.1, min(0.1, state['trend']))  # Limiter la tendance
            
            # Générer la nouvelle valeur
            noise = random.gauss(0, state['noise_level'])
            new_value = state['value'] + state['trend'] + noise
            
            # Appliquer les limites physiques
            limits = Config.SENSOR_THRESHOLDS.get(sensor_name, {})
            if 'min' in limits and 'max' in limits:
                new_value = max(limits['min'], min(limits['max'], new_value))
            
            # Occasionnellement générer des anomalies (5% de chance)
            if random.random() < 0.05:
                if random.random() < 0.5:
                    # Anomalie haute
                    new_value *= random.uniform(1.2, 1.8)
                else:
                    # Anomalie basse
                    new_value *= random.uniform(0.2, 0.8)
            
            state['value'] = new_value
            data[sensor_name] = round(new_value, 2)
        
        return data
    
    def _generate_water_level_data(self):
        """Génère des données simulées pour le capteur de niveau d'eau"""
        data = {}
        
        for sensor_name in ['water_level', 'water_temperature']:
            state = self.sensor_states[sensor_name]
            
            # Tendance et bruit
            state['trend'] += random.uniform(-0.005, 0.005)
            state['trend'] = max(-0.05, min(0.05, state['trend']))
            
            noise = random.gauss(0, state['noise_level'])
            new_value = state['value'] + state['trend'] + noise
            
            # Limites
            limits = Config.SENSOR_THRESHOLDS.get(sensor_name, {})
            if 'min' in limits and 'max' in limits:
                new_value = max(limits['min'], min(limits['max'], new_value))
            
            # Anomalies (3% de chance)
            if random.random() < 0.03:
                new_value *= random.uniform(0.3, 1.7)
            
            state['value'] = new_value
            
            # Mapping pour les clés de sortie
            if sensor_name == 'water_level':
                data['level'] = round(new_value, 1)
            elif sensor_name == 'water_temperature':
                data['temperature'] = round(new_value, 1)
        
        return data
    
    def _generate_water_flow_data(self):
        """Génère des données simulées pour le capteur de débit d'eau"""
        data = {}
        
        for sensor_name in ['water_flow', 'water_pressure']:
            state = self.sensor_states[sensor_name]
            
            # Tendance et bruit
            state['trend'] += random.uniform(-0.002, 0.002)
            state['trend'] = max(-0.02, min(0.02, state['trend']))
            
            noise = random.gauss(0, state['noise_level'])
            new_value = state['value'] + state['trend'] + noise
            
            # Limites
            limits = Config.SENSOR_THRESHOLDS.get(sensor_name, {})
            if 'min' in limits and 'max' in limits:
                new_value = max(limits['min'], min(limits['max'], new_value))
            
            # Anomalies (2% de chance)
            if random.random() < 0.02:
                new_value *= random.uniform(0.4, 1.6)
            
            state['value'] = new_value
            
            # Mapping pour les clés de sortie
            if sensor_name == 'water_flow':
                data['flow'] = round(new_value, 2)
            elif sensor_name == 'water_pressure':
                data['pressure'] = round(new_value, 2)
        
        return data
    
    def _update_system_state(self):
        """Met à jour l'état du système"""
        # Incrémenter le temps de fonctionnement
        self.system_state['uptime'] += 10  # +10 secondes
        
        # Simuler la batterie qui se décharge
        self.system_state['battery'] -= random.uniform(0.01, 0.05)
        self.system_state['battery'] = max(0, min(100, self.system_state['battery']))
        
        # Simuler la force du signal WiFi
        self.system_state['wifi_strength'] = -65 + random.randint(-10, 10)
        
        # Occasionnellement générer des erreurs système
        if random.random() < 0.01:  # 1% de chance
            error_types = [
                "Erreur de communication I2C",
                "Erreur de lecture capteur",
                "Erreur de mémoire",
                "Erreur de connexion WiFi"
            ]
            error = {
                'type': random.choice(error_types),
                'timestamp': datetime.now().isoformat(),
                'code': random.randint(100, 999)
            }
            self.system_state['errors'].append(error)
            
            # Limiter le nombre d'erreurs stockées
            if len(self.system_state['errors']) > 10:
                self.system_state['errors'] = self.system_state['errors'][-10:]

# Point d'entrée pour exécuter le simulateur directement
if __name__ == '__main__':
    simulator = ESP32Simulator()
    
    if simulator.connect():
        simulator.start()
        
        try:
            print("ESP32 Simulator: Appuyez sur Ctrl+C pour arrêter")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("ESP32 Simulator: Arrêt en cours...")
        finally:
            simulator.disconnect()
