"""
Simulateur HTTP pour remplacer le simulateur MQTT
Envoie des données via requêtes POST HTTP
"""
import time
import json
import random
import threading
import requests
from datetime import datetime, timedelta
from config import Config

class HTTPSimulator:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.endpoint = f"{base_url}/api/sensor_data"
        self.is_running = False
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
    
    def start(self):
        """Démarre la simulation"""
        if self.is_running:
            print("⚠️  Simulateur déjà démarré")
            return
            
        self.is_running = True
        
        print("🎲 Démarrage du simulateur HTTP...")
        print("📡 Envoi des données vers:", self.endpoint)
        print("📊 Les données apparaîtront ci-dessous en temps réel:")
        print("=" * 50)
        
        self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Arrête la simulation"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        print("🛑 Simulateur HTTP arrêté")
    
    def _simulation_loop(self):
        """Boucle principale de simulation"""
        cycle_count = 0
        
        while self.is_running:
            try:
                cycle_count += 1
                print(f"\n🔄 Cycle {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Simuler les données NPK 8-en-1
                npk_data = self._generate_npk_data()
                self._send_data(npk_data)
                
                time.sleep(3)
                
                if not self.is_running:
                    break
                
                # Simuler les données de niveau d'eau
                water_level_data = self._generate_water_level_data()
                self._send_data(water_level_data)
                
                time.sleep(3)
                
                if not self.is_running:
                    break
                
                # Simuler les données de débit d'eau
                water_flow_data = self._generate_water_flow_data()
                self._send_data(water_flow_data)
                
                print("-" * 30)
                time.sleep(4)  # Total 10 secondes par cycle
                
            except Exception as e:
                print(f"❌ Erreur dans la simulation: {e}")
                time.sleep(5)
        
        print("🛑 Simulation arrêtée")
    
    def _send_data(self, data):
        """Envoie les données via requête POST HTTP"""
        try:
            response = requests.post(
                self.endpoint,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ Données envoyées: {data['sensor_type']}")
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Impossible de se connecter à {self.endpoint}")
        except requests.exceptions.Timeout:
            print(f"❌ Timeout lors de l'envoi vers {self.endpoint}")
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi: {e}")
    
    def _generate_npk_data(self):
        """Génère des données simulées pour le capteur NPK 8-en-1"""
        data = {
            'sensor_type': 'npk_8in1',
            'timestamp': datetime.now().isoformat()
        }
        
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
    
    def _generate_water_level_data(self):
        """Génère des données simulées pour le capteur de niveau d'eau"""
        data = {
            'sensor_type': 'water_level',
            'timestamp': datetime.now().isoformat()
        }
        
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
        data = {
            'sensor_type': 'water_flow',
            'timestamp': datetime.now().isoformat()
        }
        
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

# Point d'entrée pour exécuter le simulateur directement
if __name__ == '__main__':
    simulator = HTTPSimulator()
    
    try:
        simulator.start()
        print("🎲 Simulateur HTTP: Appuyez sur Ctrl+C pour arrêter")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt en cours...")
    finally:
        simulator.stop()
