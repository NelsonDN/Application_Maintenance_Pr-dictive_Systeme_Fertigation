"""
Application Flask complète pour le système de maintenance prédictive FertiSmart
Version finale corrigée avec toutes les fonctionnalités
"""
import os
import json
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
import eventlet
import threading
import time

# Importer les modules du projet
from config import Config
from database import Database
from models import User
from mqtt_client import initialize_mqtt_client, get_mqtt_client
from anomaly_detector import AnomalyDetector
from predictive_maintenance import PredictiveMaintenance

# Variables globales pour éviter les doubles initialisations
mqtt_client = None
anomaly_detector = None
predictive_maintenance = None
is_initialized = False

# Initialiser l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME

# Initialiser Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

# Initialiser Flask-SocketIO avec configuration optimisée
socketio = SocketIO(
    app, 
    async_mode='eventlet',
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25
)

# Initialiser la base de données
try:
    db = Database()
    print("✅ Base de données initialisée")
except Exception as e:
    print(f"❌ Erreur d'initialisation de la base de données: {e}")
    raise

# Fonction de chargement d'utilisateur pour Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get(user_id)
    except Exception as e:
        print(f"❌ Erreur lors du chargement de l'utilisateur {user_id}: {e}")
        return None

# ==================== ROUTES D'AUTHENTIFICATION ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Veuillez saisir un nom d\'utilisateur et un mot de passe', 'warning')
            return render_template('auth/login.html')
        
        try:
            print(f"🔐 Tentative de connexion: {username}")
            user = User.get_by_username(username)
            
            if user and user.check_password(password):
                print(f"✅ Connexion réussie pour: {username}")
                login_user(user, remember=True)
                user.update_last_login()
                
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                print(f"❌ Échec de connexion pour: {username}")
                flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
                
        except Exception as e:
            print(f"❌ Erreur lors de la connexion: {e}")
            flash('Erreur lors de la connexion', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté avec succès', 'info')
    return redirect(url_for('login'))

# ==================== ROUTES PRINCIPALES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Récupérer les dernières lectures de capteurs
        recent_readings = {}
        for sensor_name in Config.SENSOR_THRESHOLDS.keys():
            try:
                readings = db.get_recent_readings(sensor_name, limit=1)
                if readings:
                    recent_readings[sensor_name] = readings[0]
            except Exception as e:
                print(f"❌ Erreur lecture capteur {sensor_name}: {e}")
        
        # Récupérer les alertes actives
        active_alerts = db.get_active_alerts(limit=5)
        
        # Récupérer les dernières prédictions
        latest_predictions = db.get_latest_predictions()
        
        # Récupérer les maintenances planifiées
        planned_maintenance = db.get_maintenance_records(status='planned', limit=3)
        
        # Calculer les statistiques RÉELLES
        all_active_alerts = db.get_active_alerts()
        all_resolved_alerts = db.get_resolved_alerts()
        
        stats = {
            'sensors_count': len(Config.SENSOR_THRESHOLDS),
            'active_alerts_count': len(all_active_alerts),
            'resolved_alerts_count': len(all_resolved_alerts),
            'total_alerts_count': len(all_active_alerts) + len(all_resolved_alerts),
            'high_risk_sensors_count': sum(1 for p in latest_predictions if float(p.get('failure_probability', 0)) > 0.6),
            'planned_maintenance_count': len(db.get_maintenance_records(status='planned'))
        }
        
        return render_template(
            'dashboard.html',
            recent_readings=recent_readings,
            active_alerts=active_alerts,
            latest_predictions=latest_predictions,
            planned_maintenance=planned_maintenance,
            stats=stats
        )
        
    except Exception as e:
        print(f"❌ Erreur dashboard: {e}")
        traceback.print_exc()
        flash('Erreur lors du chargement du dashboard', 'danger')
        return render_template('dashboard.html', 
                             recent_readings={}, 
                             active_alerts=[], 
                             latest_predictions=[], 
                             planned_maintenance=[],
                             stats={'sensors_count': 0, 'active_alerts_count': 0, 'resolved_alerts_count': 0, 'total_alerts_count': 0, 'high_risk_sensors_count': 0, 'planned_maintenance_count': 0})

@app.route('/monitoring')
@login_required
def monitoring():
    try:
        sensor_thresholds = Config.SENSOR_THRESHOLDS
        
        # Récupérer les données initiales pour les graphiques
        initial_data = {}
        for sensor_name in sensor_thresholds.keys():
            try:
                readings = db.get_recent_readings(sensor_name, limit=50)
                if readings:
                    initial_data[sensor_name] = [
                        {
                            'timestamp': reading['timestamp'],
                            'value': reading['value'],
                            'unit': reading['unit']
                        } for reading in readings
                    ]
                else:
                    initial_data[sensor_name] = []
            except Exception as e:
                print(f"❌ Erreur données initiales {sensor_name}: {e}")
                initial_data[sensor_name] = []
        
        return render_template(
            'monitoring.html',
            sensor_thresholds=sensor_thresholds,
            initial_data=json.dumps(initial_data, default=str)
        )
        
    except Exception as e:
        print(f"❌ Erreur monitoring: {e}")
        flash('Erreur lors du chargement du monitoring', 'danger')
        return render_template('monitoring.html', 
                             sensor_thresholds={}, 
                             initial_data='{}')

@app.route('/alerts')
@login_required
def alerts():
    try:
        # Récupérer les alertes avec les vraies données
        active_alerts = db.get_active_alerts()
        resolved_alerts = db.get_resolved_alerts()
        
        # Calculer le résumé des anomalies RÉEL
        anomaly_summary = {
            'total': len(active_alerts),
            'threshold': len([a for a in active_alerts if 'threshold' in a.get('alert_type', '').lower()]),
            'statistical': len([a for a in active_alerts if 'statistical' in a.get('alert_type', '').lower()]),
            'trend': len([a for a in active_alerts if 'trend' in a.get('alert_type', '').lower()]),
            'communication': len([a for a in active_alerts if 'communication' in a.get('alert_type', '').lower()])
        }
        
        return render_template(
            'alerts.html',
            active_alerts=active_alerts,
            resolved_alerts=resolved_alerts,
            anomaly_summary=anomaly_summary
        )
        
    except Exception as e:
        print(f"❌ Erreur alertes: {e}")
        traceback.print_exc()
        flash('Erreur lors du chargement des alertes', 'danger')
        return render_template('alerts.html', 
                             active_alerts=[], 
                             resolved_alerts=[], 
                             anomaly_summary={'total': 0, 'threshold': 0, 'statistical': 0, 'trend': 0, 'communication': 0})

@app.route('/maintenance')
@login_required
def maintenance():
    try:
        # Récupérer les maintenances par statut
        planned_maintenance = db.get_maintenance_records(status='planned')
        in_progress_maintenance = db.get_maintenance_records(status='in_progress')
        completed_maintenance = db.get_maintenance_records(status='completed', limit=20)
        
        # Récupérer les prédictions
        latest_predictions = db.get_latest_predictions()
        
        # Calculer les économies potentielles
        if predictive_maintenance:
            cost_savings = predictive_maintenance.calculate_maintenance_cost_savings()
        else:
            cost_savings = {
                'current_costs': 15000,
                'optimal_costs': 12000,
                'potential_savings': 3000,
                'preventive_ratio': 0.75
            }
        
        return render_template(
            'maintenance.html',
            planned_maintenance=planned_maintenance,
            in_progress_maintenance=in_progress_maintenance,
            completed_maintenance=completed_maintenance,
            latest_predictions=latest_predictions,
            cost_savings=cost_savings
        )
        
    except Exception as e:
        print(f"❌ Erreur maintenance: {e}")
        flash('Erreur lors du chargement de la maintenance', 'danger')
        return render_template('maintenance.html', 
                             planned_maintenance=[], 
                             in_progress_maintenance=[], 
                             completed_maintenance=[], 
                             latest_predictions=[], 
                             cost_savings={'current_costs': 0, 'optimal_costs': 0, 'potential_savings': 0, 'preventive_ratio': 0})

@app.route('/predictions')
@login_required
def predictions():
    try:
        # Récupérer les prédictions
        latest_predictions = db.get_latest_predictions()
        
        # Générer des recommandations
        recommendations = {}
        if predictive_maintenance:
            for prediction in latest_predictions:
                sensor_name = prediction['sensor_name']
                try:
                    sensor_recommendations = predictive_maintenance.get_maintenance_recommendations(sensor_name)
                    recommendations[sensor_name] = sensor_recommendations
                except Exception as e:
                    print(f"❌ Erreur recommandations {sensor_name}: {e}")
                    recommendations[sensor_name] = []
        
        return render_template(
            'predictions.html',
            latest_predictions=latest_predictions,
            recommendations=recommendations
        )
        
    except Exception as e:
        print(f"❌ Erreur prédictions: {e}")
        flash('Erreur lors du chargement des prédictions', 'danger')
        return render_template('predictions.html', 
                             latest_predictions=[], 
                             recommendations={})

@app.route('/configuration')
@login_required
def configuration():
    try:
        # Statut MQTT
        mqtt_status = {'connected': False, 'simulation_active': True, 'broker_host': 'localhost', 'broker_port': 1883}
        if mqtt_client:
            try:
                mqtt_status = mqtt_client.get_connection_status()
            except Exception as e:
                print(f"❌ Erreur statut MQTT: {e}")
        
        return render_template(
            'configuration.html',
            mqtt_status=mqtt_status,
            sensor_thresholds=Config.SENSOR_THRESHOLDS,
            sensor_life_parameters=Config.SENSOR_LIFE_PARAMETERS
        )
        
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        flash('Erreur lors du chargement de la configuration', 'danger')
        return render_template('configuration.html', 
                             mqtt_status={'connected': False, 'simulation_active': False}, 
                             sensor_thresholds={}, 
                             sensor_life_parameters={})

# ==================== ROUTES API ====================

@app.route('/api/alerts_count')
@login_required
def api_alerts_count():
    """API pour récupérer le nombre d'alertes actives"""
    try:
        active_alerts = db.get_active_alerts()
        return jsonify({
            'active_count': len(active_alerts),
            'success': True
        })
    except Exception as e:
        print(f"❌ Erreur API compteur alertes: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/alerts/resolve/<int:alert_id>', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    try:
        print(f"🔧 Tentative de résolution de l'alerte {alert_id}")
        success = db.resolve_alert(alert_id)
        if success:
            print(f"✅ Alerte {alert_id} résolue")
            # Émettre la mise à jour via WebSocket
            socketio.emit('alert_resolved', {'alert_id': alert_id})
            return jsonify({'success': True, 'message': 'Alerte résolue avec succès'})
        else:
            return jsonify({'success': False, 'error': 'Impossible de résoudre l\'alerte'}), 400
    except Exception as e:
        print(f"❌ Erreur résolution alerte {alert_id}: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/maintenance/update/<int:maintenance_id>', methods=['POST'])
@login_required
def update_maintenance(maintenance_id):
    try:
        status = request.form.get('status')
        if not status:
            return jsonify({'success': False, 'error': 'Statut manquant'}), 400
        
        completed_date = None
        if status == 'completed':
            completed_date = datetime.now()
        
        db.update_maintenance_status(maintenance_id, status, completed_date)
        flash(f'Maintenance mise à jour: {status}', 'success')
        return redirect(url_for('maintenance'))
        
    except Exception as e:
        print(f"❌ Erreur mise à jour maintenance {maintenance_id}: {e}")
        flash('Erreur lors de la mise à jour de la maintenance', 'danger')
        return redirect(url_for('maintenance'))

@app.route('/api/sensor_data/<sensor_name>')
@login_required
def api_sensor_data(sensor_name):
    try:
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
        
    except Exception as e:
        print(f"❌ Erreur API données capteur {sensor_name}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/run_predictive_analysis', methods=['POST'])
@login_required
def api_run_predictive_analysis():
    try:
        if not predictive_maintenance:
            return jsonify({'success': False, 'error': 'Module de maintenance prédictive non disponible'}), 500
        
        # Lancer l'analyse prédictive
        results = predictive_maintenance.run_predictive_analysis()
        
        return jsonify({
            'success': True, 
            'message': f'Analyse terminée, {results["sensors_analyzed"]} capteurs analysés',
            'results': results
        })
        
    except Exception as e:
        print(f"❌ Erreur analyse prédictive: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/force_anomaly', methods=['POST'])
@login_required
def api_force_anomaly():
    try:
        sensor_name = request.form.get('sensor_name')
        anomaly_type = request.form.get('anomaly_type')
        
        if not sensor_name or not anomaly_type:
            return jsonify({'success': False, 'error': 'Paramètres manquants'}), 400
        
        # Créer une alerte de test
        message = f"Anomalie forcée pour test: {anomaly_type}"
        severity = 'medium'
        
        alert_id = db.create_alert(sensor_name, f"test_{anomaly_type}", message, severity)
        
        # Émettre l'alerte via WebSocket
        socketio.emit('new_alert', {
            'id': alert_id,
            'sensor_name': sensor_name,
            'type': f"test_{anomaly_type}",
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'success': True, 'message': 'Anomalie de test créée'})
        
    except Exception as e:
        print(f"❌ Erreur création anomalie test: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ÉVÉNEMENTS WEBSOCKET ====================

@socketio.on('connect')
def handle_connect():
    print(f'✅ Client WebSocket connecté: {request.sid}')
    emit('connection_status', {'status': 'connected', 'timestamp': datetime.now().isoformat()})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'❌ Client WebSocket déconnecté: {request.sid}')

@socketio.on('request_sensor_data')
def handle_sensor_data_request(data):
    try:
        sensor_name = data.get('sensor_name')
        if sensor_name:
            readings = db.get_recent_readings(sensor_name, limit=10)
            emit('sensor_data_response', {'sensor_name': sensor_name, 'data': readings})
    except Exception as e:
        print(f"❌ Erreur requête données capteur: {e}")
        emit('error', {'message': 'Erreur lors de la récupération des données'})

# ==================== GESTIONNAIRES D'ERREURS ====================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    print(f"❌ Erreur interne: {error}")
    return render_template('errors/500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"❌ Exception non gérée: {e}")
    traceback.print_exc()
    return render_template('errors/500.html'), 500

# ==================== INITIALISATION DES SERVICES ====================

def initialize_services():
    """Initialise les services en arrière-plan"""
    global mqtt_client, anomaly_detector, predictive_maintenance, is_initialized
    
    if is_initialized:
        return
    
    try:
        print("🔧 Initialisation des services...")
        
        # Initialiser le détecteur d'anomalies
        anomaly_detector = AnomalyDetector()
        print("✅ Détecteur d'anomalies initialisé")
        
        # Initialiser le module de maintenance prédictive
        predictive_maintenance = PredictiveMaintenance()
        print("✅ Module de maintenance prédictive initialisé")
        
        # Initialiser le client MQTT
        mqtt_client = initialize_mqtt_client(socketio)
        print("✅ Client MQTT initialisé")
        
        # Démarrer les services MQTT
        def start_mqtt_services():
            time.sleep(3)  # Attendre que Flask soit prêt
            try:
                mqtt_client.connect()
                mqtt_client.start_simulation()
                print("✅ Services MQTT démarrés")
            except Exception as e:
                print(f"❌ Erreur démarrage MQTT: {e}")
        
        # Démarrer dans un thread séparé
        mqtt_thread = threading.Thread(target=start_mqtt_services, daemon=True)
        mqtt_thread.start()
        
        is_initialized = True
        print("✅ Tous les services initialisés")
        
    except Exception as e:
        print(f"❌ Erreur initialisation services: {e}")
        traceback.print_exc()

def create_app():
    """Crée et configure l'application"""
    # Initialiser les services
    initialize_services()
    return app, socketio

# Initialiser automatiquement au chargement du module
initialize_services()

# Point d'entrée principal
if __name__ == '__main__':
    print("⚠️  Utilisez start_app_simple.py pour un démarrage optimal")
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, use_reloader=False)
