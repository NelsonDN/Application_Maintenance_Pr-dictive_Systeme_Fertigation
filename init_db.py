#!/usr/bin/env python3
"""
Script d'initialisation de la base de données
"""
import os
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

# Créer le répertoire data s'il n'existe pas
if not os.path.exists('data'):
    os.makedirs('data')

# Connexion à la base de données
conn = sqlite3.connect('data/fertigation.db')
cursor = conn.cursor()

# Créer les tables
print("Création des tables...")

# Table des utilisateurs
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE,
    role TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
)
''')

# Table des lectures de capteurs
cursor.execute('''
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_type TEXT NOT NULL,
    sensor_name TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Table des alertes
cursor.execute('''
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_name TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
)
''')

# Table des maintenances
cursor.execute('''
CREATE TABLE IF NOT EXISTS maintenance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_name TEXT NOT NULL,
    maintenance_type TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    scheduled_date TIMESTAMP NOT NULL,
    completed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Table des prédictions
cursor.execute('''
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_name TEXT NOT NULL,
    failure_probability REAL NOT NULL,
    predicted_failure_date TIMESTAMP,
    confidence_score REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Table des statuts de capteurs
cursor.execute('''
CREATE TABLE IF NOT EXISTS sensor_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_name TEXT NOT NULL,
    status TEXT NOT NULL,
    last_maintenance_date TIMESTAMP,
    installation_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Créer l'utilisateur admin par défaut
print("Création de l'utilisateur admin...")
cursor.execute('''
INSERT OR IGNORE INTO users (username, password_hash, role)
VALUES (?, ?, ?)
''', ('admin', generate_password_hash('admin123'), 'admin'))

# Générer des données de test
print("Génération de données de test...")

# Capteurs
sensors = [
    ('npk_8in1', 'nitrogen', 'mg/kg'),
    ('npk_8in1', 'phosphorus', 'mg/kg'),
    ('npk_8in1', 'potassium', 'mg/kg'),
    ('npk_8in1', 'ph', 'pH'),
    ('npk_8in1', 'conductivity', 'µS/cm'),
    ('npk_8in1', 'temperature', '°C'),
    ('npk_8in1', 'humidity', '%'),
    ('npk_8in1', 'salinity', 'ppm'),
    ('water_level', 'water_level', '%'),
    ('water_level', 'water_temperature', '°C'),
    ('water_flow', 'water_flow', 'L/min'),
    ('water_flow', 'water_pressure', 'bar')
]

# Valeurs initiales
initial_values = {
    'nitrogen': 450.0,
    'phosphorus': 280.0,
    'potassium': 520.0,
    'ph': 7.2,
    'conductivity': 1200.0,
    'temperature': 25.0,
    'humidity': 65.0,
    'salinity': 800.0,
    'water_level': 75.0,
    'water_temperature': 24.0,
    'water_flow': 5.5,
    'water_pressure': 1.8
}

# Générer des lectures de capteurs pour les 7 derniers jours
print("Génération des lectures de capteurs...")
now = datetime.now()
for day in range(7, 0, -1):
    for hour in range(0, 24, 2):  # Une lecture toutes les 2 heures
        timestamp = now - timedelta(days=day, hours=hour)
        
        for sensor_type, sensor_name, unit in sensors:
            # Ajouter une tendance et du bruit
            base_value = initial_values[sensor_name]
            trend = (7 - day) * 0.01  # Légère tendance croissante
            noise = random.uniform(-0.05, 0.05) * base_value
            
            # Ajouter occasionnellement des anomalies
            anomaly = 0
            if random.random() < 0.05:  # 5% de chance d'anomalie
                anomaly = random.choice([-0.2, 0.2]) * base_value
            
            value = base_value * (1 + trend + noise + anomaly)
            
            cursor.execute('''
            INSERT INTO sensor_readings (sensor_type, sensor_name, value, unit, timestamp)
            VALUES (?, ?, ?, ?, ?)
            ''', (sensor_type, sensor_name, value, unit, timestamp))

# Générer quelques alertes
print("Génération des alertes...")
alert_types = ['threshold_high', 'threshold_low', 'statistical_anomaly', 'trend_anomaly']
severities = ['low', 'medium', 'high', 'critical']
messages = [
    "Valeur au-dessus du seuil maximum",
    "Valeur en-dessous du seuil minimum",
    "Anomalie statistique détectée",
    "Tendance anormale détectée",
    "Variation soudaine détectée"
]

# Alertes actives
for _ in range(5):
    sensor_name = random.choice([s[1] for s in sensors])
    alert_type = random.choice(alert_types)
    severity = random.choice(severities)
    message = random.choice(messages)
    created_at = now - timedelta(hours=random.randint(1, 24))
    
    cursor.execute('''
    INSERT INTO alerts (sensor_name, alert_type, message, severity, is_active, created_at)
    VALUES (?, ?, ?, ?, 1, ?)
    ''', (sensor_name, alert_type, message, severity, created_at))

# Alertes résolues
for _ in range(10):
    sensor_name = random.choice([s[1] for s in sensors])
    alert_type = random.choice(alert_types)
    severity = random.choice(severities)
    message = random.choice(messages)
    created_at = now - timedelta(days=random.randint(1, 7))
    resolved_at = created_at + timedelta(hours=random.randint(1, 12))
    
    cursor.execute('''
    INSERT INTO alerts (sensor_name, alert_type, message, severity, is_active, created_at, resolved_at)
    VALUES (?, ?, ?, ?, 0, ?, ?)
    ''', (sensor_name, alert_type, message, severity, created_at, resolved_at))

# Générer des maintenances
print("Génération des maintenances...")
maintenance_types = ['preventive', 'corrective', 'predictive', 'calibration']
statuses = ['planned', 'in_progress', 'completed', 'cancelled']
descriptions = [
    "Maintenance préventive régulière",
    "Remplacement du capteur",
    "Étalonnage du capteur",
    "Nettoyage du système",
    "Vérification des connexions"
]

# Maintenances planifiées
for _ in range(3):
    sensor_name = random.choice([s[1] for s in sensors])
    maintenance_type = random.choice(maintenance_types)
    description = random.choice(descriptions)
    scheduled_date = now + timedelta(days=random.randint(1, 14))
    
    cursor.execute('''
    INSERT INTO maintenance_records (sensor_name, maintenance_type, description, status, scheduled_date)
    VALUES (?, ?, ?, 'planned', ?)
    ''', (sensor_name, maintenance_type, description, scheduled_date))

# Maintenances en cours
for _ in range(2):
    sensor_name = random.choice([s[1] for s in sensors])
    maintenance_type = random.choice(maintenance_types)
    description = random.choice(descriptions)
    scheduled_date = now - timedelta(hours=random.randint(1, 12))
    
    cursor.execute('''
    INSERT INTO maintenance_records (sensor_name, maintenance_type, description, status, scheduled_date)
    VALUES (?, ?, ?, 'in_progress', ?)
    ''', (sensor_name, maintenance_type, description, scheduled_date))

# Maintenances terminées
for _ in range(5):
    sensor_name = random.choice([s[1] for s in sensors])
    maintenance_type = random.choice(maintenance_types)
    description = random.choice(descriptions)
    scheduled_date = now - timedelta(days=random.randint(7, 30))
    completed_date = scheduled_date + timedelta(hours=random.randint(1, 8))
    
    cursor.execute('''
    INSERT INTO maintenance_records (sensor_name, maintenance_type, description, status, scheduled_date, completed_date)
    VALUES (?, ?, ?, 'completed', ?, ?)
    ''', (sensor_name, maintenance_type, description, scheduled_date, completed_date))

# Générer des prédictions
print("Génération des prédictions...")
for sensor_name in [s[1] for s in sensors]:
    failure_probability = random.uniform(0.1, 0.9)
    days_until_failure = int((1 - failure_probability) * 100) + random.randint(-10, 10)
    predicted_failure_date = now + timedelta(days=days_until_failure)
    confidence_score = random.uniform(0.6, 0.95)
    
    cursor.execute('''
    INSERT INTO predictions (sensor_name, failure_probability, predicted_failure_date, confidence_score)
    VALUES (?, ?, ?, ?)
    ''', (sensor_name, failure_probability, predicted_failure_date, confidence_score))

# Générer des statuts de capteurs
print("Génération des statuts de capteurs...")
for sensor_name in [s[1] for s in sensors]:
    status = random.choice(['active', 'warning', 'error', 'maintenance'])
    last_maintenance_date = now - timedelta(days=random.randint(30, 180))
    installation_date = now - timedelta(days=random.randint(180, 365))
    
    cursor.execute('''
    INSERT INTO sensor_status (sensor_name, status, last_maintenance_date, installation_date)
    VALUES (?, ?, ?, ?)
    ''', (sensor_name, status, last_maintenance_date, installation_date))

# Valider les changements
conn.commit()

# Fermer la connexion
conn.close()

print("Initialisation de la base de données terminée avec succès!")
