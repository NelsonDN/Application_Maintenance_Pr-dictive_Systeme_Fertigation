# FertiSmart - Système de Maintenance Prédictive pour Fertigation

FertiSmart est une application web complète pour la surveillance, la détection d'anomalies et la maintenance prédictive des systèmes de fertigation en agriculture. Ce système utilise des capteurs connectés via MQTT, une analyse prédictive basée sur la loi de Weibull, et une détection d'anomalies multi-niveaux pour optimiser la maintenance des équipements.

## Fonctionnalités

- **Monitoring en temps réel** : Visualisation des données des capteurs avec des graphiques interactifs
- **Détection d'anomalies** : Identification automatique des comportements anormaux des capteurs
- **Maintenance prédictive** : Prévision des défaillances basée sur la loi de Weibull
- **Gestion des alertes** : Suivi et résolution des alertes générées par le système
- **Planification de maintenance** : Organisation des interventions préventives et correctives
- **Configuration avancée** : Paramétrage des seuils et des modèles prédictifs

## Architecture technique

- **Backend** : Flask (Python)
- **Base de données** : SQLite
- **Communication IoT** : MQTT
- **Frontend** : Bootstrap 5, Chart.js, Socket.IO
- **Analyse prédictive** : Modèle de Weibull pour la prédiction de défaillance
- **Détection d'anomalies** : Algorithmes statistiques multi-niveaux

## Structure du projet

\`\`\`
fertigation_predictive/
├── app/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/
│   ├── hhch.py                # Application Flask principale
│   ├── mqtt_client.py         # Client MQTT pour la communication avec l'ESP32
│   ├── simulator.py           # Simulateur de données pour les tests
│   ├── config.py              # Configuration du système
│   ├── database.py            # Gestion de la base de données
│   ├── models.py              # Modèles de données
│   ├── anomaly_detector.py    # Détection d'anomalies
│   └── predictive_maintenance.py  # Maintenance prédictive
└── README.md
\`\`\`

## Installation

### Prérequis

- Python 3.8+
- Pip
- Broker MQTT (optionnel, pour la connexion avec de vrais capteurs)

### Installation des dépendances

\`\`\`bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows
venv\Scripts\activate
# Sur Linux/Mac
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
\`\`\`

### Configuration

1. Copiez le fichier `config.py.example` en `config.py`
2. Modifiez les paramètres selon votre environnement

### Initialisation de la base de données

\`\`\`bash
python init_db.py
\`\`\`

### Démarrage de l'application

\`\`\`bash
python hhch.py
\`\`\`

L'application sera accessible à l'adresse http://localhost:5000

## Mode simulation

Le système inclut un simulateur de capteurs pour les tests et les démonstrations. Pour l'activer :

\`\`\`bash
python simulator.py
\`\`\`

## Utilisation

### Connexion

- Utilisateur par défaut : `admin`
- Mot de passe par défaut : `admin123`

### Pages principales

- **Dashboard** : Vue d'ensemble du système
- **Monitoring** : Visualisation en temps réel des données des capteurs
- **Alertes** : Gestion des alertes générées par le système
- **Maintenance** : Planification et suivi des opérations de maintenance
- **Prédictions** : Analyse prédictive des défaillances
- **Configuration** : Paramétrage du système

## Développement

### Structure des modules

- **hhch.py** : Point d'entrée de l'application Flask
- **mqtt_client.py** : Gestion de la communication MQTT avec les capteurs
- **simulator.py** : Génération de données simulées pour les tests
- **config.py** : Configuration globale du système
- **database.py** : Interface avec la base de données SQLite
- **models.py** : Modèles de données et classes métier
- **anomaly_detector.py** : Algorithmes de détection d'anomalies
- **predictive_maintenance.py** : Modèles prédictifs basés sur Weibull

### Ajout de nouveaux capteurs

1. Ajouter les seuils dans `config.py`
2. Mettre à jour la fonction `_initialize_sensor_states` dans `mqtt_client.py`
3. Ajouter le traitement spécifique dans les fonctions de traitement des données

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Contact

Pour toute question ou suggestion, veuillez contacter l'équipe de développement à l'adresse support@fertismart.com
\`\`\`

Enfin, créons un fichier de configuration pour Docker pour faciliter le déploiement :
