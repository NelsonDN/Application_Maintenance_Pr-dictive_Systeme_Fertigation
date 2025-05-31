# """
# Client MQTT pour la communication avec l'ESP32 et simulation des données
# """
# import json
# import time
# import threading
# import random
# from datetime import datetime, timedelta
# from typing import Dict, List, Optional, Callable
# import paho.mqtt.client as mqtt
# from config import Config
# from database import Database
# from anomaly_detector import AnomalyDetector
# import numpy as np

# class MQTTClient:
#     def __init__(self, socketio=None):
#         self.client = mqtt.Client()
#         self.db = Database()
#         self.anomaly_detector = AnomalyDetector()
#         self.socketio = socketio
#         self.is_connected = False
#         self.simulation_active = True
#         self.simulation_thread = None
        
#         # Configuration du client MQTT
#         self.client.on_connect = self.on_connect
#         self.client.on_disconnect = self.on_disconnect
#         self.client.on_message = self.on_message
        
#         # Données de simulation
#         self.sensor_states = self._initialize_sensor_states()
        
#     def _initialize_sensor_states(self) -> Dict:
#         """Initialise les états des capteurs pour la simulation"""
#         return {
#             # Capteur NPK 8-en-1
#             'nitrogen': {'value': 450.0, 'trend': 0.0, 'noise_level': 15.0},
#             'phosphorus': {'value': 280.0, 'trend': 0.0, 'noise_level': 12.0},
#             'potassium': {'value': 520.0, 'trend': 0.0, 'noise_level': 18.0},
#             'ph': {'value': 7.2, 'trend': 0.0, 'noise_level': 0.1},
#             'conductivity': {'value': 1200.0, 'trend': 0.0, 'noise_level': 50.0},
#             'temperature': {'value': 25.0, 'trend': 0.0, 'noise_level': 1.5},
#             'humidity': {'value': 65.0, 'trend': 0.0, 'noise_level': 3.0},
#             'salinity': {'value': 800.0, 'trend': 0.0, 'noise_level': 30.0},
            
#             # Capteur niveau d'eau
#             'water_level': {'value': 75.0, 'trend': 0.0, 'noise_level': 2.0},
#             'water_temperature': {'value': 24.0, 'trend': 0.0, 'noise_level': 1.0},
            
#             # Capteur débit d'eau
#             'water_flow': {'value': 5.5, 'trend': 0.0, 'noise_level': 0.3},
#             'water_pressure': {'value': 1.8, 'trend': 0.0, 'noise_level': 0.1}
#         }
    
#     def on_connect(self, client, userdata, flags, rc):
#         """Callback appelé lors de la connexion au broker MQTT"""
#         if rc == 0:
#             self.is_connected = True
#             print("Connexion MQTT réussie")
            
#             # S'abonner aux topics
#             for topic_name, topic in Config.MQTT_TOPICS.items():
#                 client.subscribe(topic)
#                 print(f"Abonnement au topic: {topic}")
                
#             # Émettre l'événement de connexion via WebSocket
#             if self.socketio:
#                 self.socketio.emit('mqtt_status', {
#                     'connected': True,
#                     'message': 'Connexion MQTT établie'
#                 })
#         else:
#             self.is_connected = False
#             print(f"Échec de connexion MQTT, code: {rc}")
            
#             if self.socketio:
#                 self.socketio.emit('mqtt_status', {
#                     'connected': False,
#                     'message': f'Échec de connexion MQTT (code: {rc})'
#                 })
    
#     def on_disconnect(self, client, userdata, rc):
#         """Callback appelé lors de la déconnexion du broker MQTT"""
#         self.is_connected = False
#         print("Déconnexion MQTT")
        
#         if self.socketio:
#             self.socketio.emit('mqtt_status', {
#                 'connected': False,
#                 'message': 'Connexion MQTT perdue'
#             })
    
#     def on_message(self, client, userdata, msg):
#         """Callback appelé lors de la réception d'un message MQTT"""
#         try:
#             topic = msg.topic
#             payload = json.loads(msg.payload.decode())
            
#             print(f"Message reçu sur {topic}: {payload}")
            
#             # Traiter le message selon le topic
#             if topic == Config.MQTT_TOPICS['npk_sensor']:
#                 self._process_npk_data(payload)
#             elif topic == Config.MQTT_TOPICS['water_level']:
#                 self._process_water_level_data(payload)
#             elif topic == Config.MQTT_TOPICS['water_flow']:
#                 self._process_water_flow_data(payload)
#             elif topic == Config.MQTT_TOPICS['system_status']:
#                 self._process_system_status(payload)
                
#         except Exception as e:
#             print(f"Erreur lors du traitement du message MQTT: {e}")
    
#     def _process_npk_data(self, data: Dict):
#         """Traite les données du capteur NPK 8-en-1"""
#         sensor_readings = []
        
#         # Mapping des données NPK
#         npk_mapping = {
#             'nitrogen': ('nitrogen', 'mg/kg'),
#             'phosphorus': ('phosphorus', 'mg/kg'),
#             'potassium': ('potassium', 'mg/kg'),
#             'ph': ('ph', 'pH'),
#             'conductivity': ('conductivity', 'µS/cm'),
#             'temperature': ('temperature', '°C'),
#             'humidity': ('humidity', '%'),
#             'salinity': ('salinity', 'ppm')
#         }
        
#         for key, (sensor_name, unit) in npk_mapping.items():
#             if key in data:
#                 reading = {
#                     'sensor_type': 'npk_8in1',
#                     'sensor_name': sensor_name,
#                     'value': float(data[key]),
#                     'unit': unit,
#                     'timestamp': datetime.now()
#                 }
#                 sensor_readings.append(reading)
                
#                 # Sauvegarder en base
#                 self.db.insert_sensor_reading(
#                     reading['sensor_type'],
#                     reading['sensor_name'],
#                     reading['value'],
#                     reading['unit']
#                 )
        
#         # Détecter les anomalies et traiter les alertes
#         self._process_sensor_readings(sensor_readings)
    
#     def _process_water_level_data(self, data: Dict):
#         """Traite les données du capteur de niveau d'eau"""
#         sensor_readings = []
        
#         water_level_mapping = {
#             'level': ('water_level', '%'),
#             'temperature': ('water_temperature', '°C')
#         }
        
#         for key, (sensor_name, unit) in water_level_mapping.items():
#             if key in data:
#                 reading = {
#                     'sensor_type': 'water_level',
#                     'sensor_name': sensor_name,
#                     'value': float(data[key]),
#                     'unit': unit,
#                     'timestamp': datetime.now()
#                 }
#                 sensor_readings.append(reading)
                
#                 # Sauvegarder en base
#                 self.db.insert_sensor_reading(
#                     reading['sensor_type'],
#                     reading['sensor_name'],
#                     reading['value'],
#                     reading['unit']
#                 )
        
#         self._process_sensor_readings(sensor_readings)
    
#     def _process_water_flow_data(self, data: Dict):
#         """Traite les données du capteur de débit d'eau"""
#         sensor_readings = []
        
#         water_flow_mapping = {
#             'flow': ('water_flow', 'L/min'),
#             'pressure': ('water_pressure', 'bar')
#         }
        
#         for key, (sensor_name, unit) in water_flow_mapping.items():
#             if key in data:
#                 reading = {
#                     'sensor_type': 'water_flow',
#                     'sensor_name': sensor_name,
#                     'value': float(data[key]),
#                     'unit': unit,
#                     'timestamp': datetime.now()
#                 }
#                 sensor_readings.append(reading)
                
#                 # Sauvegarder en base
#                 self.db.insert_sensor_reading(
#                     reading['sensor_type'],
#                     reading['sensor_name'],
#                     reading['value'],
#                     reading['unit']
#                 )
        
#         self._process_sensor_readings(sensor_readings)
    
#     def _process_system_status(self, data: Dict):
#         """Traite les données de statut du système"""
#         if self.socketio:
#             self.socketio.emit('system_status', data)
    
#     def _process_sensor_readings(self, readings: List[Dict]):
#         """Traite les lectures de capteurs pour détecter les anomalies"""
#         for reading in readings:
#             # Détecter les anomalies
#             anomalies = self.anomaly_detector.detect_all_anomalies(reading)
            
#             # Créer des alertes pour chaque anomalie détectée
#             for anomaly in anomalies:
#                 alert_id = self.db.create_alert(
#                     sensor_name=anomaly['sensor_name'],
#                     alert_type=anomaly['type'],
#                     message=anomaly['message'],
#                     severity=anomaly['severity']
#                 )
                
#                 # Émettre l'alerte via WebSocket
#                 if self.socketio:
#                     self.socketio.emit('new_alert', {
#                         'id': alert_id,
#                         'sensor_name': anomaly['sensor_name'],
#                         'type': anomaly['type'],
#                         'message': anomaly['message'],
#                         'severity': anomaly['severity'],
#                         'timestamp': datetime.now().isoformat()
#                     })
            
#             # Émettre les données en temps réel via WebSocket
#             if self.socketio:
#                 self.socketio.emit('sensor_data', {
#                     'sensor_name': reading['sensor_name'],
#                     'value': reading['value'],
#                     'unit': reading['unit'],
#                     'timestamp': reading['timestamp'].isoformat(),
#                     'anomalies_count': len(anomalies)
#                 })
    
#     def connect(self):
#         """Se connecte au broker MQTT"""
#         try:
#             self.client.connect(
#                 Config.MQTT_BROKER_HOST,
#                 Config.MQTT_BROKER_PORT,
#                 Config.MQTT_KEEPALIVE
#             )
#             self.client.loop_start()
#             print(f"Tentative de connexion au broker MQTT {Config.MQTT_BROKER_HOST}:{Config.MQTT_BROKER_PORT}")
#         except Exception as e:
#             print(f"Erreur de connexion MQTT: {e}")
#             # Démarrer la simulation si la connexion MQTT échoue
#             self.start_simulation()
    
#     def disconnect(self):
#         """Se déconnecte du broker MQTT"""
#         self.simulation_active = False
#         if self.simulation_thread:
#             self.simulation_thread.join()
        
#         if self.is_connected:
#             self.client.loop_stop()
#             self.client.disconnect()
    
#     def start_simulation(self):
#         """Démarre la simulation des données de capteurs"""
#         if not self.simulation_active:
#             return
            
#         print("Démarrage de la simulation des capteurs...")
#         self.simulation_thread = threading.Thread(target=self._simulation_loop)
#         self.simulation_thread.daemon = True
#         self.simulation_thread.start()
    
#     def _simulation_loop(self):
#         """Boucle principale de simulation"""
#         while self.simulation_active:
#             try:
#                 # Simuler les données NPK 8-en-1
#                 npk_data = self._generate_npk_data()
#                 self._process_npk_data(npk_data)
                
#                 time.sleep(2)  # Attendre 2 secondes
                
#                 # Simuler les données de niveau d'eau
#                 water_level_data = self._generate_water_level_data()
#                 self._process_water_level_data(water_level_data)
                
#                 time.sleep(2)  # Attendre 2 secondes
                
#                 # Simuler les données de débit d'eau
#                 water_flow_data = self._generate_water_flow_data()
#                 self._process_water_flow_data(water_flow_data)
                
#                 time.sleep(6)  # Attendre 6 secondes (total 10 secondes par cycle)
                
#             except Exception as e:
#                 print(f"Erreur dans la simulation: {e}")
#                 time.sleep(5)
    
#     def _generate_npk_data(self) -> Dict:
#         """Génère des données simulées pour le capteur NPK 8-en-1"""
#         data = {}
        
#         # Simuler chaque paramètre du capteur NPK
#         for sensor_name in ['nitrogen', 'phosphorus', 'potassium', 'ph', 'conductivity', 'temperature', 'humidity', 'salinity']:
#             state = self.sensor_states[sensor_name]
            
#             # Ajouter une tendance lente (dérive)
#             state['trend'] += random.uniform(-0.01, 0.01)
#             state['trend'] = max(-0.1, min(0.1, state['trend']))  # Limiter la tendance
            
#             # Générer la nouvelle valeur
#             noise = random.gauss(0, state['noise_level'])
#             new_value = state['value'] + state['trend'] + noise
            
#             # Appliquer les limites physiques
#             limits = Config.SENSOR_THRESHOLDS.get(sensor_name, {})
#             if 'min' in limits and 'max' in limits:
#                 new_value = max(limits['min'], min(limits['max'], new_value))
            
#             # Occasionnellement générer des anomalies (5% de chance)
#             if random.random() < 0.05:
#                 if random.random() < 0.5:
#                     # Anomalie haute
#                     new_value *= random.uniform(1.2, 1.8)
#                 else:
#                     # Anomalie basse
#                     new_value *= random.uniform(0.2, 0.8)
            
#             state['value'] = new_value
#             data[sensor_name] = round(new_value, 2)
        
#         return data
    
#     def _generate_water_level_data(self) -> Dict:
#         """Génère des données simulées pour le capteur de niveau d'eau"""
#         data = {}
        
#         for sensor_name in ['water_level', 'water_temperature']:
#             state = self.sensor_states[sensor_name]
            
#             # Tendance et bruit
#             state['trend'] += random.uniform(-0.005, 0.005)
#             state['trend'] = max(-0.05, min(0.05, state['trend']))
            
#             noise = random.gauss(0, state['noise_level'])
#             new_value = state['value'] + state['trend'] + noise
            
#             # Limites
#             limits = Config.SENSOR_THRESHOLDS.get(sensor_name, {})
#             if 'min' in limits and 'max' in limits:
#                 new_value = max(limits['min'], min(limits['max'], new_value))
            
#             # Anomalies (3% de chance)
#             if random.random() < 0.03:
#                 new_value *= random.uniform(0.3, 1.7)
            
#             state['value'] = new_value
            
#             # Mapping pour les clés de sortie
#             if sensor_name == 'water_level':
#                 data['level'] = round(new_value, 1)
#             elif sensor_name == 'water_temperature':
#                 data['temperature'] = round(new_value, 1)
        
#         return data
    
#     def _generate_water_flow_data(self) -> Dict:
#         """Génère des données simulées pour le capteur de débit d'eau"""
#         data = {}
        
#         for sensor_name in ['water_flow', 'water_pressure']:
#             state = self.sensor_states[sensor_name]
            
#             # Tendance et bruit
#             state['trend'] += random.uniform(-0.002, 0.002)
#             state['trend'] = max(-0.02, min(0.02, state['trend']))
            
#             noise = random.gauss(0, state['noise_level'])
#             new_value = state['value'] + state['trend'] + noise
            
#             # Limites
#             limits = Config.SENSOR_THRESHOLDS.get(sensor_name, {})
#             if 'min' in limits and 'max' in limits:
#                 new_value = max(limits['min'], min(limits['max'], new_value))
            
#             # Anomalies (2% de chance)
#             if random.random() < 0.02:
#                 new_value *= random.uniform(0.4, 1.6)
            
#             state['value'] = new_value
            
#             # Mapping pour les clés de sortie
#             if sensor_name == 'water_flow':
#                 data['flow'] = round(new_value, 2)
#             elif sensor_name == 'water_pressure':
#                 data['pressure'] = round(new_value, 2)
        
#         return data
    
#     def publish_command(self, topic: str, command: Dict):
#         """Publie une commande vers l'ESP32"""
#         if self.is_connected:
#             try:
#                 message = json.dumps(command)
#                 self.client.publish(topic, message)
#                 print(f"Commande envoyée sur {topic}: {command}")
#                 return True
#             except Exception as e:
#                 print(f"Erreur lors de l'envoi de la commande: {e}")
#                 return False
#         else:
#             print("Client MQTT non connecté")
#             return False
    
#     def get_connection_status(self) -> Dict:
#         """Retourne le statut de connexion MQTT"""
#         return {
#             'connected': self.is_connected,
#             'simulation_active': self.simulation_active,
#             'broker_host': Config.MQTT_BROKER_HOST,
#             'broker_port': Config.MQTT_BROKER_PORT
#         }
    
#     def force_anomaly(self, sensor_name: str, anomaly_type: str = 'threshold_high'):
#         """Force une anomalie pour les tests"""
#         if sensor_name in self.sensor_states:
#             state = self.sensor_states[sensor_name]
            
#             if anomaly_type == 'threshold_high':
#                 # Forcer une valeur haute
#                 limits = Config.SENSOR_THRESHOLDS.get(sensor_name, {})
#                 if 'max' in limits:
#                     state['value'] = limits['max'] * 1.5
#             elif anomaly_type == 'threshold_low':
#                 # Forcer une valeur basse
#                 limits = Config.SENSOR_THRESHOLDS.get(sensor_name, {})
#                 if 'min' in limits:
#                     state['value'] = limits['min'] * 0.5
#             elif anomaly_type == 'spike':
#                 # Créer un pic
#                 state['value'] *= 3.0
            
#             print(f"Anomalie forcée pour {sensor_name}: {anomaly_type}")
#             return True
        
#         return False

# # Instance globale du client MQTT
# mqtt_client = None

# def initialize_mqtt_client(socketio=None):
#     """Initialise le client MQTT global"""
#     global mqtt_client
#     mqtt_client = MQTTClient(socketio)
#     return mqtt_client

# def get_mqtt_client():
#     """Retourne l'instance du client MQTT"""
#     global mqtt_client
#     return mqtt_client

"""
Client MQTT pour la communication avec l'ESP32 et simulation des données
Version corrigée avec logs détaillés dans le terminal
"""
import json
import time
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import paho.mqtt.client as mqtt
from config import Config
from database import Database
from anomaly_detector import AnomalyDetector
import numpy as np

class MQTTClient:
    def __init__(self, socketio=None):
        self.client = mqtt.Client()
        self.db = Database()
        self.anomaly_detector = AnomalyDetector()
        self.socketio = socketio
        self.is_connected = False
        self.simulation_active = False
        self.simulation_thread = None
        self._simulation_started = False
        
        # Configuration du client MQTT
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        # Données de simulation
        self.sensor_states = self._initialize_sensor_states()
        
    def _initialize_sensor_states(self) -> Dict:
        """Initialise les états des capteurs pour la simulation"""
        return {
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
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback appelé lors de la connexion au broker MQTT"""
        if rc == 0:
            self.is_connected = True
            print("✅ Connexion MQTT réussie")
            
            # S'abonner aux topics
            for topic_name, topic in Config.MQTT_TOPICS.items():
                client.subscribe(topic)
                print(f"📡 Abonnement au topic: {topic}")
                
            # Émettre l'événement de connexion via WebSocket
            if self.socketio:
                self.socketio.emit('mqtt_status', {
                    'connected': True,
                    'message': 'Connexion MQTT établie'
                })
        else:
            self.is_connected = False
            print(f"❌ Échec de connexion MQTT, code: {rc}")
            
            if self.socketio:
                self.socketio.emit('mqtt_status', {
                    'connected': False,
                    'message': f'Échec de connexion MQTT (code: {rc})'
                })
    
    def on_disconnect(self, client, userdata, rc):
        """Callback appelé lors de la déconnexion du broker MQTT"""
        self.is_connected = False
        print("❌ Déconnexion MQTT")
        
        if self.socketio:
            self.socketio.emit('mqtt_status', {
                'connected': False,
                'message': 'Connexion MQTT perdue'
            })
    
    def on_message(self, client, userdata, msg):
        """Callback appelé lors de la réception d'un message MQTT"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            print(f"📨 Message reçu sur {topic}: {payload}")
            
            # Traiter le message selon le topic
            if topic == Config.MQTT_TOPICS['npk_sensor']:
                self._process_npk_data(payload)
            elif topic == Config.MQTT_TOPICS['water_level']:
                self._process_water_level_data(payload)
            elif topic == Config.MQTT_TOPICS['water_flow']:
                self._process_water_flow_data(payload)
            elif topic == Config.MQTT_TOPICS['system_status']:
                self._process_system_status(payload)
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement du message MQTT: {e}")
    
    def _process_npk_data(self, data: Dict):
        """Traite les données du capteur NPK 8-en-1"""
        sensor_readings = []
        
        # Mapping des données NPK
        npk_mapping = {
            'nitrogen': ('nitrogen', 'mg/kg'),
            'phosphorus': ('phosphorus', 'mg/kg'),
            'potassium': ('potassium', 'mg/kg'),
            'ph': ('ph', 'pH'),
            'conductivity': ('conductivity', 'µS/cm'),
            'temperature': ('temperature', '°C'),
            'humidity': ('humidity', '%'),
            'salinity': ('salinity', 'ppm')
        }
        
        for key, (sensor_name, unit) in npk_mapping.items():
            if key in data:
                reading = {
                    'sensor_type': 'npk_8in1',
                    'sensor_name': sensor_name,
                    'value': float(data[key]),
                    'unit': unit,
                    'timestamp': datetime.now()
                }
                sensor_readings.append(reading)
                
                # 🖥️ AFFICHAGE TERMINAL
                print(f"📊 {sensor_name}: {reading['value']} {unit}")
                
                # Sauvegarder en base
                self.db.insert_sensor_reading(
                    reading['sensor_type'],
                    reading['sensor_name'],
                    reading['value'],
                    reading['unit']
                )
        
        # Détecter les anomalies et traiter les alertes
        self._process_sensor_readings(sensor_readings)
    
    def _process_water_level_data(self, data: Dict):
        """Traite les données du capteur de niveau d'eau"""
        sensor_readings = []
        
        water_level_mapping = {
            'level': ('water_level', '%'),
            'temperature': ('water_temperature', '°C')
        }
        
        for key, (sensor_name, unit) in water_level_mapping.items():
            if key in data:
                reading = {
                    'sensor_type': 'water_level',
                    'sensor_name': sensor_name,
                    'value': float(data[key]),
                    'unit': unit,
                    'timestamp': datetime.now()
                }
                sensor_readings.append(reading)
                
                # 🖥️ AFFICHAGE TERMINAL
                print(f"💧 {sensor_name}: {reading['value']} {unit}")
                
                # Sauvegarder en base
                self.db.insert_sensor_reading(
                    reading['sensor_type'],
                    reading['sensor_name'],
                    reading['value'],
                    reading['unit']
                )
        
        self._process_sensor_readings(sensor_readings)
    
    def _process_water_flow_data(self, data: Dict):
        """Traite les données du capteur de débit d'eau"""
        sensor_readings = []
        
        water_flow_mapping = {
            'flow': ('water_flow', 'L/min'),
            'pressure': ('water_pressure', 'bar')
        }
        
        for key, (sensor_name, unit) in water_flow_mapping.items():
            if key in data:
                reading = {
                    'sensor_type': 'water_flow',
                    'sensor_name': sensor_name,
                    'value': float(data[key]),
                    'unit': unit,
                    'timestamp': datetime.now()
                }
                sensor_readings.append(reading)
                
                # 🖥️ AFFICHAGE TERMINAL
                print(f"🌊 {sensor_name}: {reading['value']} {unit}")
                
                # Sauvegarder en base
                self.db.insert_sensor_reading(
                    reading['sensor_type'],
                    reading['sensor_name'],
                    reading['value'],
                    reading['unit']
                )
        
        self._process_sensor_readings(sensor_readings)
    
    def _process_system_status(self, data: Dict):
        """Traite les données de statut du système"""
        if self.socketio:
            self.socketio.emit('system_status', data)
    
    def _process_sensor_readings(self, readings: List[Dict]):
        """Traite les lectures de capteurs pour détecter les anomalies"""
        for reading in readings:
            # Détecter les anomalies
            anomalies = self.anomaly_detector.detect_all_anomalies(reading)
            
            # Créer des alertes pour chaque anomalie détectée
            for anomaly in anomalies:
                alert_id = self.db.create_alert(
                    sensor_name=anomaly['sensor_name'],
                    alert_type=anomaly['type'],
                    message=anomaly['message'],
                    severity=anomaly['severity']
                )
                
                # 🚨 AFFICHAGE ALERTE TERMINAL
                print(f"🚨 ALERTE {anomaly['severity']}: {anomaly['message']}")
                
                # Émettre l'alerte via WebSocket
                if self.socketio:
                    self.socketio.emit('new_alert', {
                        'id': alert_id,
                        'sensor_name': anomaly['sensor_name'],
                        'type': anomaly['type'],
                        'message': anomaly['message'],
                        'severity': anomaly['severity'],
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Émettre les données en temps réel via WebSocket
            if self.socketio:
                self.socketio.emit('sensor_data', {
                    'sensor_name': reading['sensor_name'],
                    'value': reading['value'],
                    'unit': reading['unit'],
                    'timestamp': reading['timestamp'].isoformat(),
                    'anomalies_count': len(anomalies)
                })
    
    def connect(self):
        """Se connecte au broker MQTT"""
        try:
            self.client.connect(
                Config.MQTT_BROKER_HOST,
                Config.MQTT_BROKER_PORT,
                Config.MQTT_KEEPALIVE
            )
            self.client.loop_start()
            print(f"🔌 Tentative de connexion au broker MQTT {Config.MQTT_BROKER_HOST}:{Config.MQTT_BROKER_PORT}")
        except Exception as e:
            print(f"❌ Erreur de connexion MQTT: {e}")
            # Démarrer la simulation si la connexion MQTT échoue
            self.start_simulation()
    
    def disconnect(self):
        """Se déconnecte du broker MQTT"""
        self.simulation_active = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=2)
        
        if self.is_connected:
            self.client.loop_stop()
            self.client.disconnect()
    
    def start_simulation(self):
        """Démarre la simulation des données de capteurs"""
        if self._simulation_started or self.simulation_active:
            print("⚠️  Simulation déjà démarrée, ignoré")
            return
            
        self._simulation_started = True
        self.simulation_active = True
        
        print("🎲 Démarrage de la simulation des capteurs...")
        print("📊 Les données apparaîtront ci-dessous en temps réel:")
        print("=" * 50)
        
        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()
    
    def _simulation_loop(self):
        """Boucle principale de simulation"""
        cycle_count = 0
        
        while self.simulation_active:
            try:
                cycle_count += 1
                print(f"\n🔄 Cycle {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Simuler les données NPK 8-en-1
                npk_data = self._generate_npk_data()
                self._process_npk_data(npk_data)
                
                time.sleep(2)
                
                if not self.simulation_active:
                    break
                
                # Simuler les données de niveau d'eau
                water_level_data = self._generate_water_level_data()
                self._process_water_level_data(water_level_data)
                
                time.sleep(2)
                
                if not self.simulation_active:
                    break
                
                # Simuler les données de débit d'eau
                water_flow_data = self._generate_water_flow_data()
                self._process_water_flow_data(water_flow_data)
                
                print("-" * 30)
                time.sleep(6)  # Total 10 secondes par cycle
                
            except Exception as e:
                print(f"❌ Erreur dans la simulation: {e}")
                time.sleep(5)
        
        print("🛑 Simulation arrêtée")
    
    def _generate_npk_data(self) -> Dict:
        """Génère des données simulées pour le capteur NPK 8-en-1"""
        data = {}
        
        # Simuler chaque paramètre du capteur NPK
        for sensor_name in ['nitrogen', 'phosphorus', 'potassium', 'ph', 'conductivity', 'temperature', 'humidity', 'salinity']:
            state = self.sensor_states[sensor_name]
            
            # Ajouter une tendance lente (dérive)
            state['trend'] += random.uniform(-0.01, 0.01)
            state['trend'] = max(-0.1, min(0.1, state['trend']))
            
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
                    new_value *= random.uniform(1.2, 1.8)
                else:
                    new_value *= random.uniform(0.2, 0.8)
            
            state['value'] = new_value
            data[sensor_name] = round(new_value, 2)
        
        return data
    
    def _generate_water_level_data(self) -> Dict:
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
    
    def _generate_water_flow_data(self) -> Dict:
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
    
    def get_connection_status(self) -> Dict:
        """Retourne le statut de connexion MQTT"""
        return {
            'connected': self.is_connected,
            'simulation_active': self.simulation_active,
            'broker_host': Config.MQTT_BROKER_HOST,
            'broker_port': Config.MQTT_BROKER_PORT
        }

# Instance globale du client MQTT
mqtt_client = None

def initialize_mqtt_client(socketio=None):
    """Initialise le client MQTT global"""
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = MQTTClient(socketio)
    return mqtt_client

def get_mqtt_client():
    """Retourne l'instance du client MQTT"""
    global mqtt_client
    return mqtt_client

