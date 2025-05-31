"""
Module de maintenance prédictive utilisant la distribution de Weibull
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.stats import weibull_min
from database import Database
from config import Config
from typing import Dict, List, Optional, Tuple
import math

class PredictiveMaintenance:
    def __init__(self):
        self.db = Database()
        self.life_parameters = Config.SENSOR_LIFE_PARAMETERS
        
    def calculate_failure_probability(self, sensor_name: str, current_age_hours: float) -> Dict:
        """Calcule la probabilité de défaillance d'un capteur basée sur la distribution de Weibull"""
        
        # Mapper les noms de capteurs aux paramètres de vie
        sensor_mapping = {
            'nitrogen': 'npk_sensor',
            'phosphorus': 'npk_sensor',
            'potassium': 'npk_sensor',
            'ph': 'npk_sensor',
            'conductivity': 'npk_sensor',
            'temperature': 'npk_sensor',
            'humidity': 'npk_sensor',
            'salinity': 'npk_sensor',
            'water_level': 'water_level_sensor',
            'water_temperature': 'water_level_sensor',
            'water_flow': 'water_flow_sensor',
            'water_pressure': 'water_flow_sensor'
        }
        
        param_key = sensor_mapping.get(sensor_name, 'npk_sensor')
        
        if param_key not in self.life_parameters:
            return {
                'failure_probability': 0.0,
                'confidence_score': 0.0,
                'predicted_failure_date': None,
                'mean_time_to_failure': 0.0,
                'reliability': 1.0
            }
        
        params = self.life_parameters[param_key]
        shape = params['shape']  # β (paramètre de forme)
        scale = params['scale']  # η (paramètre d'échelle)
        
        # Calculer la fonction de répartition cumulative (CDF) - probabilité de défaillance
        failure_probability = weibull_min.cdf(current_age_hours, shape, scale=scale)
        
        # Calculer la fiabilité (1 - probabilité de défaillance)
        reliability = 1 - failure_probability
        
        # Calculer le temps moyen jusqu'à la défaillance (MTTF)
        mttf = scale * math.gamma(1 + 1/shape)
        
        # Estimer la date de défaillance probable
        if failure_probability < 0.9:
            # Temps jusqu'à 90% de probabilité de défaillance
            time_to_90_percent = weibull_min.ppf(0.9, shape, scale=scale)
            remaining_time_hours = max(0, time_to_90_percent - current_age_hours)
            predicted_failure_date = datetime.now() + timedelta(hours=remaining_time_hours)
        else:
            # Si déjà haute probabilité, défaillance imminente
            predicted_failure_date = datetime.now() + timedelta(hours=24)
        
        # Calculer le score de confiance basé sur la quantité de données historiques
        confidence_score = self._calculate_confidence_score(sensor_name)
        
        return {
            'failure_probability': float(failure_probability),
            'confidence_score': float(confidence_score),
            'predicted_failure_date': predicted_failure_date,
            'mean_time_to_failure': float(mttf),
            'reliability': float(reliability),
            'current_age_hours': float(current_age_hours),
            'shape_parameter': float(shape),
            'scale_parameter': float(scale)
        }
    
    def _calculate_confidence_score(self, sensor_name: str) -> float:
        """Calcule un score de confiance basé sur la quantité et qualité des données"""
        # Récupérer les données historiques
        recent_readings = self.db.get_recent_readings(sensor_name, limit=1000)
        
        if len(recent_readings) < 10:
            return 0.1  # Très faible confiance
        elif len(recent_readings) < 50:
            return 0.4  # Faible confiance
        elif len(recent_readings) < 200:
            return 0.7  # Confiance moyenne
        else:
            return 0.9  # Haute confiance
    
    def estimate_sensor_age(self, sensor_name: str) -> float:
        """Estime l'âge d'un capteur en heures basé sur les données disponibles"""
        # Récupérer toutes les données pour ce capteur
        all_readings = self.db.get_recent_readings(sensor_name, limit=10000)
        
        if not all_readings:
            return 0.0
        
        # Trouver la première lecture (plus ancienne)
        try:
            first_reading_time = datetime.fromisoformat(str(all_readings[-1]['timestamp']))
            current_time = datetime.now()
            age_delta = current_time - first_reading_time
            return age_delta.total_seconds() / 3600  # Convertir en heures
        except:
            # Si erreur de parsing, estimer basé sur le nombre de lectures
            # Assumer 1 lecture par minute en moyenne
            return len(all_readings) / 60.0
    
    def analyze_degradation_trend(self, sensor_name: str) -> Dict:
        """Analyse la tendance de dégradation d'un capteur"""
        readings = self.db.get_recent_readings(sensor_name, limit=200)
        
        if len(readings) < 10:
            return {
                'trend': 'INSUFFICIENT_DATA',
                'degradation_rate': 0.0,
                'trend_confidence': 0.0
            }
        
        # Convertir en DataFrame pour l'analyse
        timestamps = []
        values = []
        
        for reading in reversed(readings):  # Ordre chronologique
            try:
                timestamp = datetime.fromisoformat(str(reading['timestamp']))
                timestamps.append(timestamp)
                values.append(float(reading['value']))
            except:
                continue
        
        if len(values) < 10:
            return {
                'trend': 'INSUFFICIENT_DATA',
                'degradation_rate': 0.0,
                'trend_confidence': 0.0
            }
        
        # Convertir les timestamps en heures depuis le début
        start_time = timestamps[0]
        hours = [(t - start_time).total_seconds() / 3600 for t in timestamps]
        
        # Calculer la régression linéaire
        if len(hours) > 1:
            coefficients = np.polyfit(hours, values, 1)
            slope = coefficients[0]
            
            # Déterminer la tendance
            if abs(slope) < 0.01:
                trend = 'STABLE'
            elif slope > 0:
                trend = 'IMPROVING'
            else:
                trend = 'DEGRADING'
            
            # Calculer le coefficient de corrélation pour la confiance
            correlation = np.corrcoef(hours, values)[0, 1]
            trend_confidence = abs(correlation) if not np.isnan(correlation) else 0.0
            
            return {
                'trend': trend,
                'degradation_rate': float(slope),
                'trend_confidence': float(trend_confidence),
                'data_points': len(values)
            }
        
        return {
            'trend': 'UNKNOWN',
            'degradation_rate': 0.0,
            'trend_confidence': 0.0
        }
    
    def schedule_maintenance(self, sensor_name: str, prediction: Dict) -> Optional[int]:
        """Programme une maintenance basée sur la prédiction"""
        failure_probability = prediction['failure_probability']
        predicted_failure_date = prediction['predicted_failure_date']
        
        # Seuils pour programmer la maintenance
        if failure_probability < 0.3:
            maintenance_type = 'preventive_inspection'
            # Programmer 30 jours avant la défaillance prédite
            if predicted_failure_date:
                scheduled_date = predicted_failure_date - timedelta(days=30)
            else:
                scheduled_date = datetime.now() + timedelta(days=90)
        elif failure_probability < 0.6:
            maintenance_type = 'preventive_maintenance'
            # Programmer 14 jours avant la défaillance prédite
            if predicted_failure_date:
                scheduled_date = predicted_failure_date - timedelta(days=14)
            else:
                scheduled_date = datetime.now() + timedelta(days=30)
        elif failure_probability < 0.8:
            maintenance_type = 'urgent_maintenance'
            # Programmer 7 jours avant la défaillance prédite
            if predicted_failure_date:
                scheduled_date = predicted_failure_date - timedelta(days=7)
            else:
                scheduled_date = datetime.now() + timedelta(days=7)
        else:
            maintenance_type = 'emergency_maintenance'
            # Programmer immédiatement
            scheduled_date = datetime.now() + timedelta(hours=24)
        
        # Vérifier s'il n'y a pas déjà une maintenance programmée
        existing_maintenance = self.db.get_maintenance_records(status='planned')
        for maintenance in existing_maintenance:
            if (maintenance['sensor_name'] == sensor_name and 
                maintenance['maintenance_type'] == maintenance_type):
                return None  # Maintenance déjà programmée
        
        # Créer la description
        description = f"Maintenance {maintenance_type} pour {sensor_name}. "
        description += f"Probabilité de défaillance: {failure_probability:.1%}. "
        if predicted_failure_date:
            description += f"Défaillance prédite le: {predicted_failure_date.strftime('%Y-%m-%d %H:%M')}."
        
        # Programmer la maintenance
        maintenance_id = self.db.create_maintenance_record(
            sensor_name=sensor_name,
            maintenance_type=maintenance_type,
            description=description,
            scheduled_date=scheduled_date
        )
        
        return maintenance_id
    
    def run_predictive_analysis(self) -> Dict:
        """Exécute l'analyse prédictive pour tous les capteurs"""
        results = {
            'timestamp': datetime.now(),
            'sensors_analyzed': 0,
            'predictions': [],
            'maintenances_scheduled': 0,
            'high_risk_sensors': []
        }
        
        # Liste de tous les capteurs à analyser
        sensor_names = list(Config.SENSOR_THRESHOLDS.keys())
        
        for sensor_name in sensor_names:
            try:
                # Estimer l'âge du capteur
                sensor_age = self.estimate_sensor_age(sensor_name)
                
                if sensor_age > 0:
                    # Calculer la prédiction
                    prediction = self.calculate_failure_probability(sensor_name, sensor_age)
                    
                    # Analyser la tendance
                    trend_analysis = self.analyze_degradation_trend(sensor_name)
                    prediction.update(trend_analysis)
                    
                    # Sauvegarder la prédiction
                    self.db.save_prediction(
                        sensor_name=sensor_name,
                        failure_probability=prediction['failure_probability'],
                        predicted_failure_date=prediction['predicted_failure_date'],
                        confidence_score=prediction['confidence_score']
                    )
                    
                    # Programmer maintenance si nécessaire
                    if prediction['failure_probability'] > 0.2:
                        maintenance_id = self.schedule_maintenance(sensor_name, prediction)
                        if maintenance_id:
                            results['maintenances_scheduled'] += 1
                    
                    # Identifier les capteurs à haut risque
                    if prediction['failure_probability'] > 0.6:
                        results['high_risk_sensors'].append({
                            'sensor_name': sensor_name,
                            'failure_probability': prediction['failure_probability'],
                            'predicted_failure_date': prediction['predicted_failure_date']
                        })
                    
                    results['predictions'].append({
                        'sensor_name': sensor_name,
                        **prediction
                    })
                    
                    results['sensors_analyzed'] += 1
                    
            except Exception as e:
                print(f"Erreur lors de l'analyse du capteur {sensor_name}: {e}")
                continue
        
        return results
    
    def get_maintenance_recommendations(self, sensor_name: str) -> List[Dict]:
        """Génère des recommandations de maintenance pour un capteur"""
        recommendations = []
        
        # Obtenir la dernière prédiction
        predictions = self.db.get_latest_predictions()
        sensor_prediction = None
        
        for pred in predictions:
            if pred['sensor_name'] == sensor_name:
                sensor_prediction = pred
                break
        
        if not sensor_prediction:
            return [{
                'type': 'INFO',
                'title': 'Analyse requise',
                'description': 'Aucune prédiction disponible pour ce capteur. Exécutez une analyse prédictive.',
                'priority': 'LOW'
            }]
        
        failure_prob = sensor_prediction['failure_probability']
        
        # Recommandations basées sur la probabilité de défaillance
        if failure_prob < 0.2:
            recommendations.append({
                'type': 'PREVENTIVE',
                'title': 'Maintenance préventive standard',
                'description': 'Effectuer un contrôle visuel mensuel et calibrage trimestriel.',
                'priority': 'LOW'
            })
        elif failure_prob < 0.5:
            recommendations.extend([
                {
                    'type': 'PREVENTIVE',
                    'title': 'Inspection approfondie recommandée',
                    'description': 'Vérifier les connexions, nettoyer les capteurs et tester la précision.',
                    'priority': 'MEDIUM'
                },
                {
                    'type': 'MONITORING',
                    'title': 'Surveillance renforcée',
                    'description': 'Augmenter la fréquence de surveillance et surveiller les anomalies.',
                    'priority': 'MEDIUM'
                }
            ])
        elif failure_prob < 0.8:
            recommendations.extend([
                {
                    'type': 'URGENT',
                    'title': 'Maintenance urgente requise',
                    'description': 'Planifier une intervention dans les 7 jours. Vérifier tous les composants.',
                    'priority': 'HIGH'
                },
                {
                    'type': 'REPLACEMENT',
                    'title': 'Préparation de remplacement',
                    'description': 'Commander les pièces de rechange et préparer le remplacement du capteur.',
                    'priority': 'HIGH'
                }
            ])
        else:
            recommendations.extend([
                {
                    'type': 'EMERGENCY',
                    'title': 'Intervention d\'urgence',
                    'description': 'Risque de défaillance imminent. Intervention requise sous 24h.',
                    'priority': 'CRITICAL'
                },
                {
                    'type': 'REPLACEMENT',
                    'title': 'Remplacement immédiat',
                    'description': 'Remplacer le capteur dès que possible pour éviter l\'arrêt du système.',
                    'priority': 'CRITICAL'
                }
            ])
        
        return recommendations
    
    def calculate_maintenance_cost_savings(self) -> Dict:
        """Calcule les économies potentielles grâce à la maintenance prédictive"""
        
        # Coûts estimés (en euros)
        costs = {
            'preventive_maintenance': 100,
            'corrective_maintenance': 500,
            'emergency_repair': 1500,
            'system_downtime_per_hour': 200
        }
        
        # Analyser les maintenances des 6 derniers mois
        all_maintenances = self.db.get_maintenance_records()
        
        preventive_count = 0
        corrective_count = 0
        emergency_count = 0
        
        for maintenance in all_maintenances:
            if maintenance['maintenance_type'] in ['preventive_inspection', 'preventive_maintenance']:
                preventive_count += 1
            elif 'urgent' in maintenance['maintenance_type']:
                corrective_count += 1
            elif 'emergency' in maintenance['maintenance_type']:
                emergency_count += 1
        
        # Calculer les coûts actuels
        current_costs = (
            preventive_count * costs['preventive_maintenance'] +
            corrective_count * costs['corrective_maintenance'] +
            emergency_count * costs['emergency_repair']
        )
        
        # Estimer les économies si toutes les maintenances étaient préventives
        total_maintenances = preventive_count + corrective_count + emergency_count
        if total_maintenances > 0:
            optimal_costs = total_maintenances * costs['preventive_maintenance']
            potential_savings = current_costs - optimal_costs
        else:
            potential_savings = 0
        
        return {
            'current_costs': current_costs,
            'optimal_costs': optimal_costs if total_maintenances > 0 else 0,
            'potential_savings': max(0, potential_savings),
            'preventive_ratio': preventive_count / max(1, total_maintenances),
            'maintenance_breakdown': {
                'preventive': preventive_count,
                'corrective': corrective_count,
                'emergency': emergency_count
            }
        }