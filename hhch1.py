"""
Application Flask principale pour la maintenance prédictive du système de fertigation
"""
import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
import eventlet

# Importer les modules du projet
from config import Config
from database import Database
from models import User, SensorReading, Alert, MaintenanceRecord, Prediction, SensorStatus
from mqtt_client import initialize_mqtt_client, get_mqtt_client
from anomaly_detector import AnomalyDetector
from predictive_maintenance import PredictiveMaintenance

# Initialiser l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME

# Initialiser Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

# Initialiser Flask-SocketIO
socketio = SocketIO(app, async_mode=Config.SOCKETIO_ASYNC_MODE, cors_allowed_origins="*")

# Initialiser la base de données
db = Database()

# Initialiser le client MQTT avec SocketIO
mqtt_client = initialize_mqtt_client(socketio)

# Initialiser le détecteur d'anomalies
anomaly_detector = AnomalyDetector()

# Initialiser le module de maintenance prédictive
predictive_maintenance = PredictiveMaintenance()

# Fonction de chargement d'utilisateur pour Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Routes d'authentification
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next', url_for('dashboard'))
            return redirect(next_page)
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Route principale - Redirection vers le dashboard
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Récupérer les dernières lectures de capteurs
    recent_readings = {}
    for sensor_name in Config.SENSOR_THRESHOLDS.keys():
        readings = db.get_recent_readings(sensor_name, limit=1)
        if readings:
            recent_readings[sensor_name] = readings[0]
    
    # Récupérer les alertes actives
    active_alerts = db.get_active_alerts()
    
    # Récupérer les dernières prédictions
    latest_predictions = db.get_latest_predictions()
    
    # Récupérer les maintenances planifiées
    planned_maintenance = db.get_maintenance_records(status='planned')
    
    # Calculer les statistiques
    stats = {
        'active_alerts_count': len(active_alerts),
        'high_risk_sensors_count': sum(1 for p in latest_predictions if float(p['failure_probability']) > 0.6),
        'planned_maintenance_count': len(planned_maintenance),
        'sensors_count': len(Config.SENSOR_THRESHOLDS)
    }
    
    return render_template(
        'dashboard.html',
        recent_readings=recent_readings,
        active_alerts=active_alerts[:5],  # 5 dernières alertes
        latest_predictions=latest_predictions,
        planned_maintenance=planned_maintenance[:3],  # 3 prochaines maintenances
        stats=stats,
        mqtt_status=mqtt_client.get_connection_status()
    )

# Monitoring en temps réel
@app.route('/monitoring')
@login_required
def monitoring():
    # Récupérer les seuils de capteurs pour l'affichage
    sensor_thresholds = Config.SENSOR_THRESHOLDS
    
    # Récupérer les dernières lectures pour initialiser les graphiques
    initial_data = {}
    for sensor_name in sensor_thresholds.keys():
        readings = db.get_recent_readings(sensor_name, limit=50)
        if readings:
            initial_data[sensor_name] = [
                {
                    'timestamp': reading['timestamp'],
                    'value': reading['value'],
                    'unit': reading['unit']
                } for reading in readings
            ]
    
    return render_template(
        'monitoring.html',
        sensor_thresholds=sensor_thresholds,
        initial_data=json.dumps(initial_data),
        mqtt_status=mqtt_client.get_connection_status()
    )

# Gestion des alertes
@app.route('/alerts')
@login_required
def alerts():
    # Récupérer toutes les alertes
    all_alerts = db.get_all_alerts(limit=200)
    active_alerts = [a for a in all_alerts if a['is_active']]
    resolved_alerts = [a for a in all_alerts if not a['is_active']]
    
    # Récupérer le résumé des anomalies
    anomaly_summary = anomaly_detector.get_anomaly_summary(hours_back=24)
    
    return render_template(
        'alerts.html',
        active_alerts=active_alerts,
        resolved_alerts=resolved_alerts,
        anomaly_summary=anomaly_summary
    )

# Résoudre une alerte
@app.route('/alerts/resolve/<int:alert_id>', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    db.resolve_alert(alert_id)
    return jsonify({'success': True})

# Maintenance prédictive
@app.route('/maintenance')
@login_required
def maintenance():
    # Récupérer les enregistrements de maintenance
    planned = db.get_maintenance_records(status='planned')
    in_progress = db.get_maintenance_records(status='in_progress')
    completed = db.get_maintenance_records(status='completed')
    
    # Récupérer les dernières prédictions
    latest_predictions = db.get_latest_predictions()
    
    # Calculer les économies potentielles
    cost_savings = predictive_maintenance.calculate_maintenance_cost_savings()
    
    return render_template(
        'maintenance.html',
        planned_maintenance=planned,
        in_progress_maintenance=in_progress,
        completed_maintenance=completed,
        latest_predictions=latest_predictions,
        cost_savings=cost_savings
    )

# Mettre à jour le statut d'une maintenance
@app.route('/maintenance/update/<int:maintenance_id>', methods=['POST'])
@login_required
def update_maintenance(maintenance_id):
    status = request.form.get('status')
    completed_date = datetime.now() if status == 'completed' else None
    
    db.update_maintenance_status(maintenance_id, status, completed_date)
    return redirect(url_for('maintenance'))

# Prédictions
@app.route('/predictions')
@login_required
def predictions():
    # Récupérer les dernières prédictions
    latest_predictions = db.get_latest_predictions()
    
    # Exécuter une nouvelle analyse prédictive
    if request.args.get('refresh') == 'true':
        analysis_results = predictive_maintenance.run_predictive_analysis()
        flash('Analyse prédictive mise à jour avec succès', 'success')
        return redirect(url_for('predictions'))
    
    # Obtenir des recommandations pour chaque capteur
    recommendations = {}
    for prediction in latest_predictions:
        sensor_name = prediction['sensor_name']
        recommendations[sensor_name] = predictive_maintenance.get_maintenance_recommendations(sensor_name)
    
    return render_template(
        'predictions.html',
        latest_predictions=latest_predictions,
        recommendations=recommendations
    )

# Configuration du système
@app.route('/configuration')
@login_required
def configuration():
    return render_template(
        'configuration.html',
        mqtt_status=mqtt_client.get_connection_status(),
        sensor_thresholds=Config.SENSOR_THRESHOLDS,
        sensor_life_parameters=Config.SENSOR_LIFE_PARAMETERS
    )

# API pour les données de capteurs
@app.route('/api/sensor_data/<sensor_name>')
@login_required
def api_sensor_data(sensor_name):
    hours = int(request.args.get('hours', 24))
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    readings = db.get_readings_by_timerange(start_time, end_time, sensor_name)
    
    data = [
        {
            'timestamp': reading['timestamp'],
            'value': reading['value'],
            'unit': reading['unit']
        } for reading in readings
    ]
    
    return jsonify(data)

# API pour forcer une anomalie (pour les tests)
@app.route('/api/force_anomaly', methods=['POST'])
@login_required
def api_force_anomaly():
    sensor_name = request.form.get('sensor_name')
    anomaly_type = request.form.get('anomaly_type', 'threshold_high')
    
    success = mqtt_client.force_anomaly(sensor_name, anomaly_type)
    
    return jsonify({'success': success})

# API pour exécuter l'analyse prédictive
@app.route('/api/run_predictive_analysis', methods=['POST'])
@login_required
def api_run_predictive_analysis():
    results = predictive_maintenance.run_predictive_analysis()
    return jsonify(results)

# Événements WebSocket
@socketio.on('connect')
def handle_connect():
    print('Client connecté au WebSocket')
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client déconnecté du WebSocket')

@socketio.on('request_sensor_data')
def handle_request_sensor_data(data):
    sensor_name = data.get('sensor_name')
    if sensor_name:
        readings = db.get_recent_readings(sensor_name, limit=1)
        if readings:
            emit('sensor_data', {
                'sensor_name': sensor_name,
                'value': readings[0]['value'],
                'unit': readings[0]['unit'],
                'timestamp': readings[0]['timestamp']
            })

# Démarrer l'application
if __name__ == '__main__':
    # Démarrer la connexion MQTT seulement si ce n'est pas un redémarrage
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Premier démarrage seulement
        mqtt_client.connect()
        mqtt_client.start_simulation()
    
    # Démarrer le serveur Flask avec SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
