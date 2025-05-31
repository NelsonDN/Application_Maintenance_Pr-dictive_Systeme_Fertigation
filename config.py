# """
# Configuration de l'application Flask
# """
# import os
# from datetime import timedelta

# class Config:
#     # Configuration Flask
#     SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    
#     # Configuration base de données
#     DATABASE_PATH = 'database.db'
    
#     # Configuration MQTT
#     MQTT_BROKER_HOST = 'localhost'
#     MQTT_BROKER_PORT = 1883
#     MQTT_KEEPALIVE = 60
#     MQTT_TOPICS = {
#         'npk_sensor': 'esp32/sensors/npk',
#         'water_level': 'esp32/sensors/water_level', 
#         'water_flow': 'esp32/sensors/water_flow',
#         'system_status': 'esp32/system/status'
#     }
    
#     # Configuration Flask-Login
#     PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
#     # Configuration SocketIO
#     SOCKETIO_ASYNC_MODE = 'eventlet'
    
#     # Configuration des seuils de capteurs
#     SENSOR_THRESHOLDS = {
#         'nitrogen': {'min': 0, 'max': 1000, 'unit': 'mg/kg', 'z_score': 3.0},
#         'phosphorus': {'min': 0, 'max': 500, 'unit': 'mg/kg', 'z_score': 3.0},
#         'potassium': {'min': 0, 'max': 800, 'unit': 'mg/kg', 'z_score': 3.0},
#         'ph': {'min': 6.0, 'max': 8.5, 'unit': 'pH', 'z_score': 2.5},
#         'conductivity': {'min': 0, 'max': 2000, 'unit': 'µS/cm', 'z_score': 3.0},
#         'temperature': {'min': 15, 'max': 35, 'unit': '°C', 'z_score': 2.5},
#         'humidity': {'min': 30, 'max': 90, 'unit': '%', 'z_score': 2.5},
#         'salinity': {'min': 0, 'max': 5000, 'unit': 'ppm', 'z_score': 3.0},
#         'water_level': {'min': 5, 'max': 95, 'unit': '%', 'z_score': 2.5},
#         'water_temperature': {'min': 18, 'max': 32, 'unit': '°C', 'z_score': 2.5},
#         'water_flow': {'min': 0.2, 'max': 10, 'unit': 'L/min', 'z_score': 2.5},
#         'water_pressure': {'min': 0.5, 'max': 3.0, 'unit': 'bar', 'z_score': 2.5}
#     }
    
#     # Paramètres de maintenance prédictive (Weibull)
#     SENSOR_LIFE_PARAMETERS = {
#         'npk_sensor': {'shape': 2.5, 'scale': 8760},  # ~1 an MTBF
#         'water_level_sensor': {'shape': 1.8, 'scale': 17520},  # ~2 ans MTBF
#         'water_flow_sensor': {'shape': 2.2, 'scale': 13140}   # ~1.5 ans MTBF
#     }
    
#     # Configuration des alertes
#     ALERT_LEVELS = {
#         'INFO': 1,
#         'WARNING': 2, 
#         'CRITICAL': 3,
#         'EMERGENCY': 4
#     }

"""
Configuration du système de maintenance prédictive
"""
import os
from datetime import timedelta

class Config:
    # Configuration Flask
    SECRET_KEY = 'votre-cle-secrete-ici-changez-la-en-production'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Configuration de la base de données
    DATABASE_PATH = os.path.join('data', 'fertigation.db')
    
    # Configuration MQTT
    MQTT_BROKER_HOST = 'localhost'
    MQTT_BROKER_PORT = 1883
    MQTT_KEEPALIVE = 60
    
    # Topics MQTT
    MQTT_TOPICS = {
        'npk_sensor': 'esp32/sensors/npk',
        'water_level': 'esp32/sensors/water_level',
        'water_flow': 'esp32/sensors/water_flow',
        'system_status': 'esp32/system/status'
    }
    
    # Seuils des capteurs pour la détection d'anomalies
    SENSOR_THRESHOLDS = {
        'nitrogen': {
            'min': 200.0,
            'max': 800.0,
            'unit': 'mg/kg',
            'z_score': 2.5
        },
        'phosphorus': {
            'min': 100.0,
            'max': 500.0,
            'unit': 'mg/kg',
            'z_score': 2.5
        },
        'potassium': {
            'min': 300.0,
            'max': 900.0,
            'unit': 'mg/kg',
            'z_score': 2.5
        },
        'ph': {
            'min': 5.5,
            'max': 8.5,
            'unit': 'pH',
            'z_score': 2.0
        },
        'conductivity': {
            'min': 500.0,
            'max': 2000.0,
            'unit': 'µS/cm',
            'z_score': 2.5
        },
        'temperature': {
            'min': 10.0,
            'max': 40.0,
            'unit': '°C',
            'z_score': 2.0
        },
        'humidity': {
            'min': 30.0,
            'max': 90.0,
            'unit': '%',
            'z_score': 2.0
        },
        'salinity': {
            'min': 200.0,
            'max': 1500.0,
            'unit': 'ppm',
            'z_score': 2.5
        },
        'water_level': {
            'min': 10.0,
            'max': 100.0,
            'unit': '%',
            'z_score': 2.0
        },
        'water_temperature': {
            'min': 15.0,
            'max': 35.0,
            'unit': '°C',
            'z_score': 2.0
        },
        'water_flow': {
            'min': 1.0,
            'max': 15.0,
            'unit': 'L/min',
            'z_score': 2.5
        },
        'water_pressure': {
            'min': 0.5,
            'max': 3.0,
            'unit': 'bar',
            'z_score': 2.0
        }
    }
    
    # Paramètres de durée de vie des capteurs (pour la loi de Weibull)
    SENSOR_LIFE_PARAMETERS = {
        'nitrogen': {
            'shape': 2.5,  # Paramètre de forme (β)
            'scale': 8760,  # Paramètre d'échelle (η) en heures (1 an)
            'location': 0   # Paramètre de localisation (γ)
        },
        'phosphorus': {
            'shape': 2.2,
            'scale': 8760,
            'location': 0
        },
        'potassium': {
            'shape': 2.8,
            'scale': 7000,
            'location': 0
        },
        'ph': {
            'shape': 1.8,
            'scale': 6000,
            'location': 0
        },
        'conductivity': {
            'shape': 2.0,
            'scale': 9000,
            'location': 0
        },
        'temperature': {
            'shape': 3.0,
            'scale': 10000,
            'location': 0
        },
        'humidity': {
            'shape': 2.3,
            'scale': 8000,
            'location': 0
        },
        'salinity': {
            'shape': 2.1,
            'scale': 7500,
            'location': 0
        },
        'water_level': {
            'shape': 1.9,
            'scale': 5000,
            'location': 0
        },
        'water_temperature': {
            'shape': 2.7,
            'scale': 9500,
            'location': 0
        },
        'water_flow': {
            'shape': 1.5,
            'scale': 4000,
            'location': 0
        },
        'water_pressure': {
            'shape': 2.4,
            'scale': 6500,
            'location': 0
        }
    }
    
    # Configuration des alertes
    ALERT_SEVERITIES = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4
    }
    
    # Configuration de la maintenance prédictive
    MAINTENANCE_THRESHOLDS = {
        'failure_probability_warning': 0.3,
        'failure_probability_critical': 0.7,
        'days_ahead_warning': 30,
        'days_ahead_critical': 7
    }
    
    # Configuration des logs
    LOG_LEVEL = 'INFO'
    LOG_FILE = os.path.join('data', 'fertigation.log')
    
    # Configuration de l'interface
    REFRESH_INTERVAL = 30  # secondes
    MAX_CHART_POINTS = 100
    
    # Configuration de sécurité
    SESSION_COOKIE_SECURE = False  # True en production avec HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
