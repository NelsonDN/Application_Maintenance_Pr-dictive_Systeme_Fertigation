# """
# Module de détection d'anomalies pour les capteurs
# """
# import numpy as np
# import pandas as pd
# from datetime import datetime, timedelta
# from database import Database
# from config import Config
# from typing import List, Dict, Tuple, Optional

# class AnomalyDetector:
#     def __init__(self):
#         self.db = Database()
#         self.thresholds = Config.SENSOR_THRESHOLDS
        
#     def detect_all_anomalies(self, sensor_reading: Dict) -> List[Dict]:
#         """Détecte tous les types d'anomalies pour une lecture de capteur"""
#         anomalies = []
        
#         # Anomalies de valeur (seuils)
#         threshold_anomaly = self.detect_threshold_anomaly(sensor_reading)
#         if threshold_anomaly:
#             anomalies.append(threshold_anomaly)
        
#         # Anomalies statistiques (Z-score)
#         statistical_anomaly = self.detect_statistical_anomaly(sensor_reading)
#         if statistical_anomaly:
#             anomalies.append(statistical_anomaly)
        
#         # Anomalies de tendance
#         trend_anomaly = self.detect_trend_anomaly(sensor_reading)
#         if trend_anomaly:
#             anomalies.append(trend_anomaly)
        
#         # Anomalies de communication
#         comm_anomaly = self.detect_communication_anomaly(sensor_reading)
#         if comm_anomaly:
#             anomalies.append(comm_anomaly)
        
#         return anomalies
    
#     def detect_threshold_anomaly(self, sensor_reading: Dict) -> Optional[Dict]:
#         """Détecte les anomalies de seuil"""
#         sensor_name = sensor_reading['sensor_name']
#         value = sensor_reading['value']
        
#         if sensor_name in self.thresholds:
#             threshold = self.thresholds[sensor_name]
#             min_val = threshold['min']
#             max_val = threshold['max']
            
#             if value < min_val:
#                 return {
#                     'type': 'THRESHOLD_LOW',
#                     'sensor_name': sensor_name,
#                     'message': f"{sensor_name} en dessous du seuil minimum: {value} {threshold['unit']} < {min_val} {threshold['unit']}",
#                     'severity': 3,  # CRITICAL
#                     'value': value,
#                     'threshold': min_val
#                 }
#             elif value > max_val:
#                 return {
#                     'type': 'THRESHOLD_HIGH',
#                     'sensor_name': sensor_name,
#                     'message': f"{sensor_name} au-dessus du seuil maximum: {value} {threshold['unit']} > {max_val} {threshold['unit']}",
#                     'severity': 3,  # CRITICAL
#                     'value': value,
#                     'threshold': max_val
#                 }
        
#         return None
    
#     def detect_statistical_anomaly(self, sensor_reading: Dict) -> Optional[Dict]:
#         """Détecte les anomalies statistiques basées sur le Z-score"""
#         sensor_name = sensor_reading['sensor_name']
#         current_value = sensor_reading['value']
        
#         # Récupérer les 100 dernières lectures pour calculer les statistiques
#         recent_readings = self.db.get_recent_readings(sensor_name, limit=100)
        
#         if len(recent_readings) < 10:  # Pas assez de données
#             return None
        
#         values = [float(reading['value']) for reading in recent_readings]
#         mean = np.mean(values)
#         std = np.std(values)
        
#         if std == 0:  # Éviter la division par zéro
#             return None
        
#         z_score = abs((current_value - mean) / std)
        
#         if sensor_name in self.thresholds:
#             threshold_z = self.thresholds[sensor_name].get('z_score', 3.0)
#         else:
#             threshold_z = 3.0
        
#         if z_score > threshold_z:
#             return {
#                 'type': 'STATISTICAL_ANOMALY',
#                 'sensor_name': sensor_name,
#                 'message': f"Anomalie statistique détectée pour {sensor_name}: Z-score = {z_score:.2f}",
#                 'severity': 2,  # WARNING
#                 'value': current_value,
#                 'z_score': z_score,
#                 'mean': mean,
#                 'std': std
#             }
        
#         return None
    
#     def detect_trend_anomaly(self, sensor_reading: Dict) -> Optional[Dict]:
#         """Détecte les anomalies de tendance (changements brusques)"""
#         sensor_name = sensor_reading['sensor_name']
#         current_value = sensor_reading['value']
        
#         # Récupérer les 20 dernières lectures
#         recent_readings = self.db.get_recent_readings(sensor_name, limit=20)
        
#         if len(recent_readings) < 5:
#             return None
        
#         values = [float(reading['value']) for reading in recent_readings]
        
#         # Calculer la dérivée (taux de changement)
#         derivatives = []
#         for i in range(1, len(values)):
#             derivatives.append(abs(values[i] - values[i-1]))
        
#         if not derivatives:
#             return None
        
#         mean_derivative = np.mean(derivatives)
#         current_derivative = abs(current_value - values[0])
        
#         # Si le changement actuel est 5 fois plus important que la moyenne
#         if mean_derivative > 0 and current_derivative > 5 * mean_derivative:
#             return {
#                 'type': 'TREND_ANOMALY',
#                 'sensor_name': sensor_name,
#                 'message': f"Changement brusque détecté pour {sensor_name}: variation de {current_derivative:.2f}",
#                 'severity': 2,  # WARNING
#                 'value': current_value,
#                 'change_rate': current_derivative,
#                 'average_change': mean_derivative
#             }
        
#         return None
    
#     def detect_communication_anomaly(self, sensor_reading: Dict) -> Optional[Dict]:
#         """Détecte les anomalies de communication"""
#         sensor_name = sensor_reading['sensor_name']
#         current_time = datetime.now()
        
#         # Récupérer la dernière lecture avant celle-ci
#         recent_readings = self.db.get_recent_readings(sensor_name, limit=2)
        
#         if len(recent_readings) < 2:
#             return None
        
#         try:
#             last_timestamp = datetime.fromisoformat(str(recent_readings[1]['timestamp']))
#             time_diff = current_time - last_timestamp
            
#             # Si plus de 5 minutes sans communication
#             if time_diff > timedelta(minutes=5):
#                 return {
#                     'type': 'COMMUNICATION_ANOMALY',
#                     'sensor_name': sensor_name,
#                     'message': f"Perte de communication prolongée pour {sensor_name}: {time_diff.total_seconds()/60:.1f} minutes",
#                     'severity': 2,  # WARNING
#                     'time_gap': time_diff.total_seconds()
#                 }
#         except Exception as e:
#             # Erreur de parsing de la date
#             return {
#                 'type': 'TIMESTAMP_ERROR',
#                 'sensor_name': sensor_name,
#                 'message': f"Erreur de timestamp pour {sensor_name}: {str(e)}",
#                 'severity': 1  # INFO
#             }
        
#         return None
    
#     def detect_correlation_anomaly(self, sensor_readings: List[Dict]) -> List[Dict]:
#         """Détecte les anomalies de corrélation entre capteurs"""
#         anomalies = []
        
#         # Vérifier la corrélation température-humidité pour le capteur NPK
#         temp_reading = None
#         humidity_reading = None
        
#         for reading in sensor_readings:
#             if reading['sensor_name'] == 'temperature':
#                 temp_reading = reading
#             elif reading['sensor_name'] == 'humidity':
#                 humidity_reading = reading
        
#         if temp_reading and humidity_reading:
#             temp = temp_reading['value']
#             humidity = humidity_reading['value']
            
#             # Corrélation inverse attendue: haute température -> basse humidité
#             if temp > 30 and humidity > 80:
#                 anomalies.append({
#                     'type': 'CORRELATION_ANOMALY',
#                     'sensor_name': 'temperature_humidity',
#                     'message': f"Corrélation anormale: Température élevée ({temp}°C) avec humidité élevée ({humidity}%)",
#                     'severity': 2,  # WARNING
#                     'temperature': temp,
#                     'humidity': humidity
#                 })
        
#         return anomalies
    
#     def detect_calibration_anomaly(self, sensor_reading: Dict) -> Optional[Dict]:
#         """Détecte les anomalies de calibration (valeurs impossibles)"""
#         sensor_name = sensor_reading['sensor_name']
#         value = sensor_reading['value']
        
#         # Définir des limites physiques absolues
#         absolute_limits = {
#             'ph': {'min': 0, 'max': 14},
#             'temperature': {'min': -50, 'max': 100},
#             'humidity': {'min': 0, 'max': 100},
#             'water_level': {'min': 0, 'max': 100},
#             'conductivity': {'min': 0, 'max': 10000},
#             'nitrogen': {'min': 0, 'max': 5000},
#             'phosphorus': {'min': 0, 'max': 2000},
#             'potassium': {'min': 0, 'max': 3000}
#         }
        
#         if sensor_name in absolute_limits:
#             limits = absolute_limits[sensor_name]
#             if value < limits['min'] or value > limits['max']:
#                 return {
#                     'type': 'CALIBRATION_ANOMALY',
#                     'sensor_name': sensor_name,
#                     'message': f"Valeur physiquement impossible pour {sensor_name}: {value}",
#                     'severity': 3,  # CRITICAL
#                     'value': value,
#                     'physical_limits': limits
#                 }
        
#         return None
    
#     def get_anomaly_summary(self, hours_back: int = 24) -> Dict[str, int]:
#         """Obtient un résumé des anomalies sur les dernières heures"""
#         start_time = datetime.now() - timedelta(hours=hours_back)
#         end_time = datetime.now()
        
#         alerts = self.db.get_all_alerts(limit=1000)
        
#         # Filtrer les alertes dans la période
#         recent_alerts = []
#         for alert in alerts:
#             try:
#                 alert_time = datetime.fromisoformat(str(alert['created_at']))
#                 if start_time <= alert_time <= end_time:
#                     recent_alerts.append(alert)
#             except:
#                 continue
        
#         # Compter par type
#         summary = {
#             'total': len(recent_alerts),
#             'threshold': 0,
#             'statistical': 0,
#             'trend': 0,
#             'communication': 0,
#             'correlation': 0,
#             'calibration': 0
#         }
        
#         for alert in recent_alerts:
#             alert_type = alert['alert_type'].lower()
#             if 'threshold' in alert_type:
#                 summary['threshold'] += 1
#             elif 'statistical' in alert_type:
#                 summary['statistical'] += 1
#             elif 'trend' in alert_type:
#                 summary['trend'] += 1
#             elif 'communication' in alert_type:
#                 summary['communication'] += 1
#             elif 'correlation' in alert_type:
#                 summary['correlation'] += 1
#             elif 'calibration' in alert_type:
#                 summary['calibration'] += 1
        
#         return summary
    
#     def get_sensor_health_score(self, sensor_name: str) -> float:
#         """Calcule un score de santé pour un capteur (0-100)"""
#         # Récupérer les alertes récentes pour ce capteur
#         alerts = self.db.get_all_alerts(limit=100)
#         recent_alerts = [a for a in alerts if a['sensor_name'] == sensor_name and a['is_active']]
        
#         # Score de base
#         score = 100.0
        
#         # Pénalités par type d'alerte
#         for alert in recent_alerts:
#             severity = alert['severity']
#             if severity == 4:  # EMERGENCY
#                 score -= 25
#             elif severity == 3:  # CRITICAL
#                 score -= 15
#             elif severity == 2:  # WARNING
#                 score -= 8
#             elif severity == 1:  # INFO
#                 score -= 3
        
#         # Vérifier la régularité des données
#         recent_readings = self.db.get_recent_readings(sensor_name, limit=10)
#         if len(recent_readings) < 5:
#             score -= 20  # Pénalité pour manque de données
        
#         return max(0.0, min(100.0, score))


"""
Module de détection d'anomalies pour les capteurs - Version corrigée
"""
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import Config
from database import Database

class AnomalyDetector:
    def __init__(self):
        self.db = Database()
        self.thresholds = Config.SENSOR_THRESHOLDS
        self.historical_data = {}  # Cache pour les données historiques
        self.last_communication = {}  # Suivi de la dernière communication
    
    def detect_all_anomalies(self, reading: Dict) -> List[Dict]:
        """Détecte toutes les anomalies pour une lecture de capteur"""
        anomalies = []
        sensor_name = reading['sensor_name']
        
        # ✅ Mettre à jour la dernière communication
        self.last_communication[sensor_name] = datetime.now()
        
        # Vérifier les anomalies de seuil
        threshold_anomaly = self.detect_threshold_anomaly(reading)
        if threshold_anomaly:
            anomalies.append(threshold_anomaly)
        
        # Vérifier les anomalies statistiques (seulement si assez de données)
        statistical_anomaly = self.detect_statistical_anomaly(reading)
        if statistical_anomaly:
            anomalies.append(statistical_anomaly)
        
        # ❌ DÉSACTIVER les alertes de communication pour la simulation
        # Les alertes de communication ne sont pas pertinentes en mode simulation
        
        return anomalies
    
    def detect_threshold_anomaly(self, reading: Dict) -> Optional[Dict]:
        """Détecte les anomalies de dépassement de seuil"""
        sensor_name = reading['sensor_name']
        value = reading['value']
        
        if sensor_name not in self.thresholds:
            return None
        
        threshold = self.thresholds[sensor_name]
        
        if 'min' in threshold and value < threshold['min']:
            return {
                'sensor_name': sensor_name,
                'type': 'threshold_low',
                'message': f"{sensor_name} en dessous du seuil minimum: {value} {reading['unit']} < {threshold['min']} {reading['unit']}",
                'severity': 'high'
            }
        
        if 'max' in threshold and value > threshold['max']:
            return {
                'sensor_name': sensor_name,
                'type': 'threshold_high',
                'message': f"{sensor_name} au-dessus du seuil maximum: {value} {reading['unit']} > {threshold['max']} {reading['unit']}",
                'severity': 'high'
            }
        
        return None
    
    def detect_statistical_anomaly(self, reading: Dict) -> Optional[Dict]:
        """Détecte les anomalies statistiques (valeurs aberrantes)"""
        sensor_name = reading['sensor_name']
        value = reading['value']
        
        if sensor_name not in self.thresholds:
            return None
        
        # Récupérer les données historiques
        historical_data = self._get_historical_data(sensor_name, hours=2)
        if len(historical_data) < 10:  # Pas assez de données
            return None
        
        # Calculer la moyenne et l'écart-type
        values = [data['value'] for data in historical_data]
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:  # Éviter la division par zéro
            return None
        
        # Calculer le z-score
        z_score = abs(value - mean) / std
        
        # Vérifier si le z-score dépasse le seuil (plus permissif)
        threshold_z = 4.0  # Seuil plus élevé pour éviter trop d'alertes
        
        if z_score > threshold_z:
            return {
                'sensor_name': sensor_name,
                'type': 'statistical_anomaly',
                'message': f"Valeur {value} {reading['unit']} statistiquement anormale pour {sensor_name} (z-score: {z_score:.2f})",
                'severity': 'medium'
            }
        
        return None
    
    def detect_trend_anomaly(self, reading: Dict) -> Optional[Dict]:
        """Détecte les anomalies de tendance (changements rapides)"""
        sensor_name = reading['sensor_name']
        value = reading['value']
        
        # Récupérer les données historiques récentes
        historical_data = self._get_historical_data(sensor_name, hours=2)
        if len(historical_data) < 5:  # Pas assez de données
            return None
        
        # Calculer la tendance (pente)
        recent_values = [data['value'] for data in historical_data[:5]]
        if len(set(recent_values)) <= 1:  # Pas de variation
            return None
        
        # Calculer le taux de variation
        avg_recent = np.mean(recent_values)
        if avg_recent == 0:  # Éviter la division par zéro
            return None
        
        rate_of_change = abs(value - avg_recent) / avg_recent
        
        # Seuil de variation rapide (20%)
        if rate_of_change > 0.2:
            severity = 'low' if rate_of_change < 0.3 else 'medium' if rate_of_change < 0.5 else 'high'
            return {
                'sensor_name': sensor_name,
                'type': 'trend_anomaly',
                'message': f"Variation rapide détectée ({rate_of_change*100:.1f}% de changement)",
                'severity': severity
            }
        
        return None
    
    def detect_communication_loss(self) -> List[Dict]:
        """
        Détecte les pertes de communication (DÉSACTIVÉ en mode simulation)
        Cette méthode peut être appelée périodiquement pour vérifier les communications
        """
        # ❌ DÉSACTIVÉ pour éviter les fausses alertes en simulation
        return []
    
    def _get_historical_data(self, sensor_name: str, hours: int = 24) -> List[Dict]:
        """Récupère les données historiques pour un capteur"""
        # Utiliser le cache si disponible
        cache_key = f"{sensor_name}_{hours}"
        if cache_key in self.historical_data:
            # Vérifier si les données sont récentes (moins de 5 minutes)
            if datetime.now() - self.historical_data[cache_key]['timestamp'] < timedelta(minutes=5):
                return self.historical_data[cache_key]['data']
        
        # Récupérer les données de la base
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        data = self.db.get_readings_by_timerange(start_time, end_time, sensor_name)
        
        # Mettre en cache
        self.historical_data[cache_key] = {
            'timestamp': datetime.now(),
            'data': data
        }
        
        return data
