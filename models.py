"""
Modèles de données pour l'application de maintenance prédictive
"""
import hashlib
from datetime import datetime
from flask_login import UserMixin
from database import Database

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, role, created_at=None, last_login=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at
        self.last_login = last_login
    
    def check_password(self, password):
        """Vérifie si le mot de passe fourni correspond au hash stocké"""
        # ✅ Utiliser la même méthode de hachage que dans database.py
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.password_hash
    
    def is_admin(self):
        """Vérifie si l'utilisateur est administrateur"""
        return self.role == 'admin'
    
    @staticmethod
    def get(user_id):
        """Récupère un utilisateur par son ID"""
        db = Database()
        user_data = db.get_user_by_id(user_id)
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                role=user_data['role'],
                created_at=user_data['created_at'],
                last_login=user_data['last_login']
            )
        return None
    
    @staticmethod
    def get_by_username(username):
        """Récupère un utilisateur par son nom d'utilisateur"""
        db = Database()
        user_data = db.get_user_by_username(username)
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                role=user_data['role'],
                created_at=user_data['created_at'],
                last_login=user_data['last_login']
            )
        return None
    
    @staticmethod
    def create(username, email, password, role='user'):
        """Crée un nouvel utilisateur"""
        db = Database()
        return db.create_user(username, email, password, role)
    
    def update_last_login(self):
        """Met à jour la dernière connexion"""
        db = Database()
        db.update_last_login(self.id)
        self.last_login = datetime.now()

class SensorReading:
    def __init__(self, id, sensor_type, sensor_name, value, unit, timestamp):
        self.id = id
        self.sensor_type = sensor_type
        self.sensor_name = sensor_name
        self.value = value
        self.unit = unit
        self.timestamp = timestamp
    
    @staticmethod
    def get_recent(sensor_name=None, limit=100):
        """Récupère les lectures récentes"""
        db = Database()
        return db.get_recent_readings(sensor_name, limit)
    
    @staticmethod
    def get_by_timerange(start_time, end_time, sensor_name=None):
        """Récupère les lectures dans une plage de temps"""
        db = Database()
        return db.get_readings_by_timerange(start_time, end_time, sensor_name)

class Alert:
    def __init__(self, id, sensor_name, alert_type, message, severity, is_active, created_at, resolved_at=None):
        self.id = id
        self.sensor_name = sensor_name
        self.alert_type = alert_type
        self.message = message
        self.severity = severity
        self.is_active = is_active
        self.created_at = created_at
        self.resolved_at = resolved_at
    
    @staticmethod
    def get_active(limit=None):
        """Récupère les alertes actives"""
        db = Database()
        return db.get_active_alerts(limit)
    
    @staticmethod
    def get_resolved(limit=None):
        """Récupère les alertes résolues"""
        db = Database()
        return db.get_resolved_alerts(limit)
    
    @staticmethod
    def create(sensor_name, alert_type, message, severity):
        """Crée une nouvelle alerte"""
        db = Database()
        return db.create_alert(sensor_name, alert_type, message, severity)
    
    def resolve(self):
        """Marque l'alerte comme résolue"""
        db = Database()
        db.resolve_alert(self.id)
        self.is_active = False
        self.resolved_at = datetime.now()

class MaintenanceRecord:
    def __init__(self, id, sensor_name, maintenance_type, description, scheduled_date, 
                 completed_date=None, status='planned', created_at=None):
        self.id = id
        self.sensor_name = sensor_name
        self.maintenance_type = maintenance_type
        self.description = description
        self.scheduled_date = scheduled_date
        self.completed_date = completed_date
        self.status = status
        self.created_at = created_at
    
    @staticmethod
    def get_by_status(status=None, limit=None):
        """Récupère les maintenances par statut"""
        db = Database()
        return db.get_maintenance_records(status, limit)
    
    @staticmethod
    def create(sensor_name, maintenance_type, description, scheduled_date):
        """Crée un nouvel enregistrement de maintenance"""
        db = Database()
        return db.create_maintenance_record(sensor_name, maintenance_type, description, scheduled_date)
    
    def update_status(self, status, completed_date=None):
        """Met à jour le statut de la maintenance"""
        db = Database()
        db.update_maintenance_status(self.id, status, completed_date)
        self.status = status
        if completed_date:
            self.completed_date = completed_date

class Prediction:
    def __init__(self, id, sensor_name, failure_probability, predicted_failure_date, 
                 confidence_score, created_at):
        self.id = id
        self.sensor_name = sensor_name
        self.failure_probability = failure_probability
        self.predicted_failure_date = predicted_failure_date
        self.confidence_score = confidence_score
        self.created_at = created_at
    
    @staticmethod
    def get_latest():
        """Récupère les dernières prédictions"""
        db = Database()
        return db.get_latest_predictions()
    
    @staticmethod
    def save(sensor_name, failure_probability, predicted_failure_date, confidence_score):
        """Sauvegarde une nouvelle prédiction"""
        db = Database()
        return db.save_prediction(sensor_name, failure_probability, predicted_failure_date, confidence_score)




# """
# Modèles de données pour l'application
# """
# from flask_login import UserMixin
# from database import Database

# class User(UserMixin):
#     def __init__(self, id, username, email, password_hash, created_at):
#         self.id = id
#         self.username = username
#         self.email = email
#         self.password_hash = password_hash
#         self.created_at = created_at
    
#     @staticmethod
#     def get(user_id):
#         """Récupère un utilisateur par son ID"""
#         db = Database()
#         user_data = db.get_user_by_id(user_id)
#         if user_data:
#             return User(
#                 id=user_data['id'],
#                 username=user_data['username'],
#                 email=user_data['email'],
#                 password_hash=user_data['password_hash'],
#                 created_at=user_data['created_at']
#             )
#         return None
    
#     @staticmethod
#     def get_by_username(username):
#         """Récupère un utilisateur par son nom d'utilisateur"""
#         db = Database()
#         user_data = db.get_user_by_username(username)
#         if user_data:
#             return User(
#                 id=user_data['id'],
#                 username=user_data['username'],
#                 email=user_data['email'],
#                 password_hash=user_data['password_hash'],
#                 created_at=user_data['created_at']
#             )
#         return None
    
#     def check_password(self, password):
#         """Vérifie le mot de passe"""
#         import hashlib
#         password_hash = hashlib.sha256(password.encode()).hexdigest()
#         return password_hash == self.password_hash

# class SensorReading:
#     def __init__(self, id, sensor_type, sensor_name, value, unit, timestamp):
#         self.id = id
#         self.sensor_type = sensor_type
#         self.sensor_name = sensor_name
#         self.value = value
#         self.unit = unit
#         self.timestamp = timestamp
    
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'sensor_type': self.sensor_type,
#             'sensor_name': self.sensor_name,
#             'value': self.value,
#             'unit': self.unit,
#             'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp)
#         }

# class Alert:
#     def __init__(self, id, sensor_name, alert_type, message, severity, is_active, created_at, resolved_at=None):
#         self.id = id
#         self.sensor_name = sensor_name
#         self.alert_type = alert_type
#         self.message = message
#         self.severity = severity
#         self.is_active = is_active
#         self.created_at = created_at
#         self.resolved_at = resolved_at
    
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'sensor_name': self.sensor_name,
#             'alert_type': self.alert_type,
#             'message': self.message,
#             'severity': self.severity,
#             'is_active': self.is_active,
#             'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else str(self.created_at),
#             'resolved_at': self.resolved_at.isoformat() if self.resolved_at and hasattr(self.resolved_at, 'isoformat') else self.resolved_at,
#             'severity_text': self.severity_text,
#             'severity_class': self.severity_class
#         }
    
#     @property
#     def severity_text(self):
#         severity_map = {1: 'INFO', 2: 'WARNING', 3: 'CRITICAL', 4: 'EMERGENCY'}
#         return severity_map.get(self.severity, 'UNKNOWN')
    
#     @property
#     def severity_class(self):
#         class_map = {1: 'info', 2: 'warning', 3: 'danger', 4: 'dark'}
#         return class_map.get(self.severity, 'secondary')

# class MaintenanceRecord:
#     def __init__(self, id, sensor_name, maintenance_type, description, scheduled_date, completed_date, status):
#         self.id = id
#         self.sensor_name = sensor_name
#         self.maintenance_type = maintenance_type
#         self.description = description
#         self.scheduled_date = scheduled_date
#         self.completed_date = completed_date
#         self.status = status
    
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'sensor_name': self.sensor_name,
#             'maintenance_type': self.maintenance_type,
#             'description': self.description,
#             'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date and hasattr(self.scheduled_date, 'isoformat') else str(self.scheduled_date),
#             'completed_date': self.completed_date.isoformat() if self.completed_date and hasattr(self.completed_date, 'isoformat') else self.completed_date,
#             'status': self.status,
#             'status_class': self.status_class
#         }
    
#     @property
#     def status_class(self):
#         class_map = {
#             'planned': 'primary',
#             'in_progress': 'warning',
#             'completed': 'success',
#             'cancelled': 'secondary'
#         }
#         return class_map.get(self.status, 'secondary')

# class Prediction:
#     def __init__(self, id, sensor_name, failure_probability, predicted_failure_date, confidence_score, created_at):
#         self.id = id
#         self.sensor_name = sensor_name
#         self.failure_probability = failure_probability
#         self.predicted_failure_date = predicted_failure_date
#         self.confidence_score = confidence_score
#         self.created_at = created_at
    
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'sensor_name': self.sensor_name,
#             'failure_probability': self.failure_probability,
#             'predicted_failure_date': self.predicted_failure_date.isoformat() if self.predicted_failure_date and hasattr(self.predicted_failure_date, 'isoformat') else self.predicted_failure_date,
#             'confidence_score': self.confidence_score,
#             'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else str(self.created_at),
#             'risk_level': self.risk_level,
#             'risk_class': self.risk_class,
#             'days_until_failure': self.days_until_failure
#         }
    
#     @property
#     def risk_level(self):
#         """Détermine le niveau de risque basé sur la probabilité de défaillance"""
#         if self.failure_probability < 0.2:
#             return 'FAIBLE'
#         elif self.failure_probability < 0.5:
#             return 'MOYEN'
#         elif self.failure_probability < 0.8:
#             return 'ÉLEVÉ'
#         else:
#             return 'CRITIQUE'
    
#     @property
#     def risk_class(self):
#         """Classe CSS pour le niveau de risque"""
#         risk_class_map = {
#             'FAIBLE': 'success',
#             'MOYEN': 'warning',
#             'ÉLEVÉ': 'danger',
#             'CRITIQUE': 'dark'
#         }
#         return risk_class_map.get(self.risk_level, 'secondary')
    
#     @property
#     def days_until_failure(self):
#         """Calcule le nombre de jours jusqu'à la défaillance prédite"""
#         if not self.predicted_failure_date:
#             return None
        
#         from datetime import datetime
#         try:
#             if isinstance(self.predicted_failure_date, str):
#                 pred_date = datetime.fromisoformat(self.predicted_failure_date.replace('Z', '+00:00'))
#             else:
#                 pred_date = self.predicted_failure_date
            
#             now = datetime.now()
#             delta = pred_date - now
#             return max(0, delta.days)
#         except:
#             return None

# class SensorStatus:
#     """Classe pour représenter le statut d'un capteur"""
#     def __init__(self, sensor_name, sensor_type, last_reading=None, is_active=True, last_communication=None):
#         self.sensor_name = sensor_name
#         self.sensor_type = sensor_type
#         self.last_reading = last_reading
#         self.is_active = is_active
#         self.last_communication = last_communication
    
#     def to_dict(self):
#         return {
#             'sensor_name': self.sensor_name,
#             'sensor_type': self.sensor_type,
#             'last_reading': self.last_reading.to_dict() if self.last_reading else None,
#             'is_active': self.is_active,
#             'last_communication': self.last_communication.isoformat() if self.last_communication and hasattr(self.last_communication, 'isoformat') else str(self.last_communication),
#             'status_class': self.status_class,
#             'status_text': self.status_text
#         }
    
#     @property
#     def status_class(self):
#         """Classe CSS pour le statut du capteur"""
#         if not self.is_active:
#             return 'danger'
#         elif self.last_communication:
#             from datetime import datetime, timedelta
#             try:
#                 if isinstance(self.last_communication, str):
#                     last_comm = datetime.fromisoformat(self.last_communication.replace('Z', '+00:00'))
#                 else:
#                     last_comm = self.last_communication
                
#                 time_diff = datetime.now() - last_comm
#                 if time_diff > timedelta(minutes=10):
#                     return 'warning'
#                 else:
#                     return 'success'
#             except:
#                 return 'secondary'
#         else:
#             return 'secondary'
    
#     @property
#     def status_text(self):
#         """Texte du statut du capteur"""
#         if not self.is_active:
#             return 'INACTIF'
#         elif self.last_communication:
#             from datetime import datetime, timedelta
#             try:
#                 if isinstance(self.last_communication, str):
#                     last_comm = datetime.fromisoformat(self.last_communication.replace('Z', '+00:00'))
#                 else:
#                     last_comm = self.last_communication
                
#                 time_diff = datetime.now() - last_comm
#                 if time_diff > timedelta(minutes=10):
#                     return 'COMMUNICATION PERDUE'
#                 else:
#                     return 'ACTIF'
#             except:
#                 return 'STATUT INCONNU'
#         else:
#             return 'STATUT INCONNU'