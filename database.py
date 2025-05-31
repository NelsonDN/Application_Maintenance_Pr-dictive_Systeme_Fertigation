"""
Gestion de la base de données SQLite - Version corrigée avec chemin sécurisé
"""
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path=None):
        # ✅ Chemin par défaut sécurisé
        if db_path is None:
            db_path = os.path.join('data', 'fertigation.db')
        
        self.db_path = db_path
        self.ensure_db_exists()
        self.init_database()
    
    def ensure_db_exists(self):
        """S'assure que le répertoire de la base de données existe"""
        db_dir = os.path.dirname(self.db_path)
        
        # ✅ Vérifier que le répertoire n'est pas vide
        if db_dir and not os.path.exists(db_dir):
            print(f"📁 Création du répertoire: {db_dir}")
            os.makedirs(db_dir)
    
    def get_connection(self):
        """Obtient une connexion à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table des utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Table des données de capteurs
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
                description TEXT,
                scheduled_date TIMESTAMP,
                completed_date TIMESTAMP,
                status TEXT DEFAULT 'planned',
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
                confidence_score REAL,
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
        
        conn.commit()
        conn.close()
        
        # Créer un utilisateur admin par défaut
        self.create_default_user()
    
    def create_default_user(self):
        """Crée un utilisateur admin par défaut"""
        try:
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@fertigation.com', password_hash, 'admin'))
            conn.commit()
            conn.close()
            print("👤 Utilisateur admin créé/vérifié")
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'utilisateur par défaut: {e}")
    
    # ==================== MÉTHODES POUR LES UTILISATEURS ====================
    
    def get_user_by_username(self, username):
        """Récupère un utilisateur par son nom d'utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def get_user_by_id(self, user_id):
        """Récupère un utilisateur par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def create_user(self, username, email, password, role='user'):
        """Crée un nouveau utilisateur"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def update_last_login(self, user_id):
        """Met à jour la dernière connexion d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now(), user_id))
        conn.commit()
        conn.close()
    
    # ==================== MÉTHODES POUR LES CAPTEURS ====================
    
    def insert_sensor_reading(self, sensor_type, sensor_name, value, unit):
        """Insère une nouvelle lecture de capteur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sensor_readings (sensor_type, sensor_name, value, unit)
            VALUES (?, ?, ?, ?)
        ''', (sensor_type, sensor_name, value, unit))
        conn.commit()
        conn.close()
    
    def get_recent_readings(self, sensor_name=None, limit=100):
        """Récupère les lectures récentes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if sensor_name:
            cursor.execute('''
                SELECT * FROM sensor_readings 
                WHERE sensor_name = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (sensor_name, limit))
        else:
            cursor.execute('''
                SELECT * FROM sensor_readings 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        readings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return readings
    
    def get_readings_by_timerange(self, start_time, end_time, sensor_name=None):
        """Récupère les lectures dans une plage de temps"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if sensor_name:
            cursor.execute('''
                SELECT * FROM sensor_readings 
                WHERE sensor_name = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            ''', (sensor_name, start_time, end_time))
        else:
            cursor.execute('''
                SELECT * FROM sensor_readings 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            ''', (start_time, end_time))
        
        readings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return readings
    
    # ==================== MÉTHODES POUR LES ALERTES ====================
    
    def create_alert(self, sensor_name, alert_type, message, severity):
        """Crée une nouvelle alerte"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO alerts (sensor_name, alert_type, message, severity)
            VALUES (?, ?, ?, ?)
        ''', (sensor_name, alert_type, message, severity))
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return alert_id
    
    def get_active_alerts(self, limit=None):
        """Récupère les alertes actives"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM alerts 
            WHERE is_active = 1 
            ORDER BY created_at DESC
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query)
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            # Ajouter des classes CSS pour l'affichage
            alert['severity_class'] = self._get_severity_class(alert['severity'])
            alert['severity_text'] = alert['severity'].upper()
            alerts.append(alert)
        
        conn.close()
        return alerts
    
    def get_resolved_alerts(self, limit=None):
        """Récupère les alertes résolues"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM alerts 
            WHERE is_active = 0 
            ORDER BY resolved_at DESC
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query)
        
        alerts = []
        for row in cursor.fetchall():
            alert = dict(row)
            alert['severity_class'] = 'resolved'
            alert['severity_text'] = 'RÉSOLU'
            alerts.append(alert)
        
        conn.close()
        return alerts
    
    def get_all_alerts(self, limit=200):
        """Récupère toutes les alertes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM alerts 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return alerts
    
    def resolve_alert(self, alert_id):
        """Marque une alerte comme résolue"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE alerts 
            SET is_active = 0, resolved_at = ? 
            WHERE id = ?
        ''', (datetime.now(), alert_id))
        conn.commit()
        conn.close()
    
    # ==================== MÉTHODES POUR LA MAINTENANCE ====================
    
    def create_maintenance_record(self, sensor_name, maintenance_type, description, scheduled_date):
        """Crée un enregistrement de maintenance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO maintenance_records 
            (sensor_name, maintenance_type, description, scheduled_date)
            VALUES (?, ?, ?, ?)
        ''', (sensor_name, maintenance_type, description, scheduled_date))
        maintenance_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return maintenance_id
    
    def get_maintenance_records(self, status=None, limit=None):
        """Récupère les enregistrements de maintenance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            query = '''
                SELECT * FROM maintenance_records 
                WHERE status = ? 
                ORDER BY scheduled_date DESC
            '''
            params = (status,)
        else:
            query = '''
                SELECT * FROM maintenance_records 
                ORDER BY scheduled_date DESC
            '''
            params = ()
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query, params)
        
        records = []
        for row in cursor.fetchall():
            record = dict(row)
            record['status_class'] = self._get_status_class(record['status'])
            records.append(record)
        
        conn.close()
        return records
    
    def update_maintenance_status(self, maintenance_id, status, completed_date=None):
        """Met à jour le statut d'une maintenance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if completed_date:
            cursor.execute('''
                UPDATE maintenance_records 
                SET status = ?, completed_date = ? 
                WHERE id = ?
            ''', (status, completed_date, maintenance_id))
        else:
            cursor.execute('''
                UPDATE maintenance_records 
                SET status = ? 
                WHERE id = ?
            ''', (status, maintenance_id))
        
        conn.commit()
        conn.close()
    
    # ==================== MÉTHODES POUR LES PRÉDICTIONS ====================
    
    def save_prediction(self, sensor_name, failure_probability, predicted_failure_date, confidence_score):
        """Sauvegarde une prédiction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions 
            (sensor_name, failure_probability, predicted_failure_date, confidence_score)
            VALUES (?, ?, ?, ?)
        ''', (sensor_name, failure_probability, predicted_failure_date, confidence_score))
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return prediction_id
    
    def get_latest_predictions(self):
        """Récupère les dernières prédictions pour chaque capteur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p1.* FROM predictions p1
            INNER JOIN (
                SELECT sensor_name, MAX(created_at) as max_date
                FROM predictions
                GROUP BY sensor_name
            ) p2 ON p1.sensor_name = p2.sensor_name AND p1.created_at = p2.max_date
        ''')
        
        predictions = []
        for row in cursor.fetchall():
            prediction = dict(row)
            # Ajouter des informations calculées
            prediction['risk_level'] = self._get_risk_level(prediction['failure_probability'])
            prediction['risk_class'] = self._get_risk_class(prediction['failure_probability'])
            
            # Calculer les jours restants
            if prediction['predicted_failure_date']:
                try:
                    failure_date = datetime.fromisoformat(prediction['predicted_failure_date'])
                    days_left = (failure_date - datetime.now()).days
                    prediction['days_until_failure'] = max(0, days_left)
                except:
                    prediction['days_until_failure'] = None
            else:
                prediction['days_until_failure'] = None
            
            predictions.append(prediction)
        
        conn.close()
        return predictions
    
    # ==================== MÉTHODES UTILITAIRES ====================
    
    def _get_severity_class(self, severity: str) -> str:
        """Retourne la classe CSS pour une sévérité"""
        mapping = {
            'low': 'info',
            'medium': 'warning', 
            'high': 'danger',
            'critical': 'dark'
        }
        return mapping.get(severity.lower(), 'info')
    
    def _get_risk_level(self, probability: float) -> str:
        """Retourne le niveau de risque"""
        if probability < 0.3:
            return 'FAIBLE'
        elif probability < 0.6:
            return 'MOYEN'
        elif probability < 0.8:
            return 'ÉLEVÉ'
        else:
            return 'CRITIQUE'
    
    def _get_risk_class(self, probability: float) -> str:
        """Retourne la classe CSS pour le risque"""
        if probability < 0.3:
            return 'success'
        elif probability < 0.6:
            return 'info'
        elif probability < 0.8:
            return 'warning'
        else:
            return 'danger'
    
    def _get_status_class(self, status: str) -> str:
        """Retourne la classe CSS pour un statut"""
        mapping = {
            'planned': 'primary',
            'in_progress': 'warning',
            'completed': 'success',
            'cancelled': 'secondary'
        }
        return mapping.get(status, 'secondary')

if __name__ == '__main__':
    # Test de la base de données
    print("🧪 Test de la base de données...")
    db = Database()
    print("✅ Base de données initialisée avec succès!")
    print("👤 Utilisateur par défaut créé: admin / admin123")


# """
# Gestion de la base de données SQLite - Version complète corrigée
# """
# import sqlite3
# import hashlib
# import os
# from datetime import datetime, timedelta
# from typing import List, Dict, Optional
# from config import Config

# class Database:
#     def __init__(self, db_path=None):
#         self.db_path = db_path or Config.DATABASE_PATH
#         self.ensure_db_exists()
#         self.init_database()
    
#     def ensure_db_exists(self):
#         """S'assure que le répertoire de la base de données existe"""
#         if not os.path.exists(os.path.dirname(self.db_path)):
#             os.makedirs(os.path.dirname(self.db_path))
    
#     def get_connection(self):
#         """Obtient une connexion à la base de données"""
#         conn = sqlite3.connect(self.db_path)
#         conn.row_factory = sqlite3.Row
#         return conn
    
#     def init_database(self):
#         """Initialise la base de données avec les tables nécessaires"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         # Table des utilisateurs
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS users (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 username TEXT UNIQUE NOT NULL,
#                 email TEXT UNIQUE NOT NULL,
#                 password_hash TEXT NOT NULL,
#                 role TEXT DEFAULT 'user',
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 last_login TIMESTAMP
#             )
#         ''')
        
#         # Table des données de capteurs
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS sensor_readings (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 sensor_type TEXT NOT NULL,
#                 sensor_name TEXT NOT NULL,
#                 value REAL NOT NULL,
#                 unit TEXT NOT NULL,
#                 timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         # Table des alertes
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS alerts (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 sensor_name TEXT NOT NULL,
#                 alert_type TEXT NOT NULL,
#                 message TEXT NOT NULL,
#                 severity TEXT NOT NULL,
#                 is_active BOOLEAN DEFAULT 1,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 resolved_at TIMESTAMP
#             )
#         ''')
        
#         # Table des maintenances
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS maintenance_records (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 sensor_name TEXT NOT NULL,
#                 maintenance_type TEXT NOT NULL,
#                 description TEXT,
#                 scheduled_date TIMESTAMP,
#                 completed_date TIMESTAMP,
#                 status TEXT DEFAULT 'planned',
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         # Table des prédictions
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS predictions (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 sensor_name TEXT NOT NULL,
#                 failure_probability REAL NOT NULL,
#                 predicted_failure_date TIMESTAMP,
#                 confidence_score REAL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         # Table des statuts de capteurs
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS sensor_status (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 sensor_name TEXT NOT NULL,
#                 status TEXT NOT NULL,
#                 last_maintenance_date TIMESTAMP,
#                 installation_date TIMESTAMP,
#                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         conn.commit()
#         conn.close()
        
#         # Créer un utilisateur admin par défaut
#         self.create_default_user()
    
#     def create_default_user(self):
#         """Crée un utilisateur admin par défaut"""
#         try:
#             password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
#             conn = self.get_connection()
#             cursor = conn.cursor()
#             cursor.execute('''
#                 INSERT OR IGNORE INTO users (username, email, password_hash, role)
#                 VALUES (?, ?, ?, ?)
#             ''', ('admin', 'admin@fertigation.com', password_hash, 'admin'))
#             conn.commit()
#             conn.close()
#         except Exception as e:
#             print(f"Erreur lors de la création de l'utilisateur par défaut: {e}")
    
#     # ==================== MÉTHODES POUR LES UTILISATEURS ====================
    
#     def get_user_by_username(self, username):
#         """Récupère un utilisateur par son nom d'utilisateur"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
#         user = cursor.fetchone()
#         conn.close()
#         return user
    
#     def get_user_by_id(self, user_id):
#         """Récupère un utilisateur par son ID"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
#         user = cursor.fetchone()
#         conn.close()
#         return user
    
#     def create_user(self, username, email, password, role='user'):
#         """Crée un nouveau utilisateur"""
#         password_hash = hashlib.sha256(password.encode()).hexdigest()
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         try:
#             cursor.execute('''
#                 INSERT INTO users (username, email, password_hash, role)
#                 VALUES (?, ?, ?, ?)
#             ''', (username, email, password_hash, role))
#             conn.commit()
#             return True
#         except sqlite3.IntegrityError:
#             return False
#         finally:
#             conn.close()
    
#     def update_last_login(self, user_id):
#         """Met à jour la dernière connexion d'un utilisateur"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             UPDATE users SET last_login = ? WHERE id = ?
#         ''', (datetime.now(), user_id))
#         conn.commit()
#         conn.close()
    
#     # ==================== MÉTHODES POUR LES CAPTEURS ====================
    
#     def insert_sensor_reading(self, sensor_type, sensor_name, value, unit):
#         """Insère une nouvelle lecture de capteur"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT INTO sensor_readings (sensor_type, sensor_name, value, unit)
#             VALUES (?, ?, ?, ?)
#         ''', (sensor_type, sensor_name, value, unit))
#         conn.commit()
#         conn.close()
    
#     def get_recent_readings(self, sensor_name=None, limit=100):
#         """Récupère les lectures récentes"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         if sensor_name:
#             cursor.execute('''
#                 SELECT * FROM sensor_readings 
#                 WHERE sensor_name = ? 
#                 ORDER BY timestamp DESC 
#                 LIMIT ?
#             ''', (sensor_name, limit))
#         else:
#             cursor.execute('''
#                 SELECT * FROM sensor_readings 
#                 ORDER BY timestamp DESC 
#                 LIMIT ?
#             ''', (limit,))
        
#         readings = [dict(row) for row in cursor.fetchall()]
#         conn.close()
#         return readings
    
#     def get_readings_by_timerange(self, start_time, end_time, sensor_name=None):
#         """Récupère les lectures dans une plage de temps"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         if sensor_name:
#             cursor.execute('''
#                 SELECT * FROM sensor_readings 
#                 WHERE sensor_name = ? AND timestamp BETWEEN ? AND ?
#                 ORDER BY timestamp ASC
#             ''', (sensor_name, start_time, end_time))
#         else:
#             cursor.execute('''
#                 SELECT * FROM sensor_readings 
#                 WHERE timestamp BETWEEN ? AND ?
#                 ORDER BY timestamp ASC
#             ''', (start_time, end_time))
        
#         readings = [dict(row) for row in cursor.fetchall()]
#         conn.close()
#         return readings
    
#     # ==================== MÉTHODES POUR LES ALERTES ====================
    
#     def create_alert(self, sensor_name, alert_type, message, severity):
#         """Crée une nouvelle alerte"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT INTO alerts (sensor_name, alert_type, message, severity)
#             VALUES (?, ?, ?, ?)
#         ''', (sensor_name, alert_type, message, severity))
#         alert_id = cursor.lastrowid
#         conn.commit()
#         conn.close()
#         return alert_id
    
#     def get_active_alerts(self, limit=None):
#         """Récupère les alertes actives"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         query = '''
#             SELECT * FROM alerts 
#             WHERE is_active = 1 
#             ORDER BY created_at DESC
#         '''
        
#         if limit:
#             query += f' LIMIT {limit}'
        
#         cursor.execute(query)
        
#         alerts = []
#         for row in cursor.fetchall():
#             alert = dict(row)
#             # Ajouter des classes CSS pour l'affichage
#             alert['severity_class'] = self._get_severity_class(alert['severity'])
#             alert['severity_text'] = alert['severity'].upper()
#             alerts.append(alert)
        
#         conn.close()
#         return alerts
    
#     def get_resolved_alerts(self, limit=None):
#         """Récupère les alertes résolues"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         query = '''
#             SELECT * FROM alerts 
#             WHERE is_active = 0 
#             ORDER BY resolved_at DESC
#         '''
        
#         if limit:
#             query += f' LIMIT {limit}'
        
#         cursor.execute(query)
        
#         alerts = []
#         for row in cursor.fetchall():
#             alert = dict(row)
#             alert['severity_class'] = 'resolved'
#             alert['severity_text'] = 'RÉSOLU'
#             alerts.append(alert)
        
#         conn.close()
#         return alerts
    
#     def get_all_alerts(self, limit=200):
#         """Récupère toutes les alertes"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             SELECT * FROM alerts 
#             ORDER BY created_at DESC 
#             LIMIT ?
#         ''', (limit,))
#         alerts = [dict(row) for row in cursor.fetchall()]
#         conn.close()
#         return alerts
    
#     def resolve_alert(self, alert_id):
#         """Marque une alerte comme résolue"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             UPDATE alerts 
#             SET is_active = 0, resolved_at = ? 
#             WHERE id = ?
#         ''', (datetime.now(), alert_id))
#         conn.commit()
#         conn.close()
    
#     # ==================== MÉTHODES POUR LA MAINTENANCE ====================
    
#     def create_maintenance_record(self, sensor_name, maintenance_type, description, scheduled_date):
#         """Crée un enregistrement de maintenance"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT INTO maintenance_records 
#             (sensor_name, maintenance_type, description, scheduled_date)
#             VALUES (?, ?, ?, ?)
#         ''', (sensor_name, maintenance_type, description, scheduled_date))
#         maintenance_id = cursor.lastrowid
#         conn.commit()
#         conn.close()
#         return maintenance_id
    
#     def get_maintenance_records(self, status=None, limit=None):
#         """Récupère les enregistrements de maintenance"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         if status:
#             query = '''
#                 SELECT * FROM maintenance_records 
#                 WHERE status = ? 
#                 ORDER BY scheduled_date DESC
#             '''
#             params = (status,)
#         else:
#             query = '''
#                 SELECT * FROM maintenance_records 
#                 ORDER BY scheduled_date DESC
#             '''
#             params = ()
        
#         if limit:
#             query += f' LIMIT {limit}'
        
#         cursor.execute(query, params)
        
#         records = []
#         for row in cursor.fetchall():
#             record = dict(row)
#             record['status_class'] = self._get_status_class(record['status'])
#             records.append(record)
        
#         conn.close()
#         return records
    
#     def update_maintenance_status(self, maintenance_id, status, completed_date=None):
#         """Met à jour le statut d'une maintenance"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         if completed_date:
#             cursor.execute('''
#                 UPDATE maintenance_records 
#                 SET status = ?, completed_date = ? 
#                 WHERE id = ?
#             ''', (status, completed_date, maintenance_id))
#         else:
#             cursor.execute('''
#                 UPDATE maintenance_records 
#                 SET status = ? 
#                 WHERE id = ?
#             ''', (status, maintenance_id))
        
#         conn.commit()
#         conn.close()
    
#     # ==================== MÉTHODES POUR LES PRÉDICTIONS ====================
    
#     def save_prediction(self, sensor_name, failure_probability, predicted_failure_date, confidence_score):
#         """Sauvegarde une prédiction"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT INTO predictions 
#             (sensor_name, failure_probability, predicted_failure_date, confidence_score)
#             VALUES (?, ?, ?, ?)
#         ''', (sensor_name, failure_probability, predicted_failure_date, confidence_score))
#         prediction_id = cursor.lastrowid
#         conn.commit()
#         conn.close()
#         return prediction_id
    
#     def get_latest_predictions(self):
#         """Récupère les dernières prédictions pour chaque capteur"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             SELECT p1.* FROM predictions p1
#             INNER JOIN (
#                 SELECT sensor_name, MAX(created_at) as max_date
#                 FROM predictions
#                 GROUP BY sensor_name
#             ) p2 ON p1.sensor_name = p2.sensor_name AND p1.created_at = p2.max_date
#         ''')
        
#         predictions = []
#         for row in cursor.fetchall():
#             prediction = dict(row)
#             # Ajouter des informations calculées
#             prediction['risk_level'] = self._get_risk_level(prediction['failure_probability'])
#             prediction['risk_class'] = self._get_risk_class(prediction['failure_probability'])
            
#             # Calculer les jours restants
#             if prediction['predicted_failure_date']:
#                 try:
#                     failure_date = datetime.fromisoformat(prediction['predicted_failure_date'])
#                     days_left = (failure_date - datetime.now()).days
#                     prediction['days_until_failure'] = max(0, days_left)
#                 except:
#                     prediction['days_until_failure'] = None
#             else:
#                 prediction['days_until_failure'] = None
            
#             predictions.append(prediction)
        
#         conn.close()
#         return predictions
    
#     # ==================== MÉTHODES UTILITAIRES ====================
    
#     def _get_severity_class(self, severity: str) -> str:
#         """Retourne la classe CSS pour une sévérité"""
#         mapping = {
#             'low': 'info',
#             'medium': 'warning', 
#             'high': 'danger',
#             'critical': 'dark'
#         }
#         return mapping.get(severity.lower(), 'info')
    
#     def _get_risk_level(self, probability: float) -> str:
#         """Retourne le niveau de risque"""
#         if probability < 0.3:
#             return 'FAIBLE'
#         elif probability < 0.6:
#             return 'MOYEN'
#         elif probability < 0.8:
#             return 'ÉLEVÉ'
#         else:
#             return 'CRITIQUE'
    
#     def _get_risk_class(self, probability: float) -> str:
#         """Retourne la classe CSS pour le risque"""
#         if probability < 0.3:
#             return 'success'
#         elif probability < 0.6:
#             return 'info'
#         elif probability < 0.8:
#             return 'warning'
#         else:
#             return 'danger'
    
#     def _get_status_class(self, status: str) -> str:
#         """Retourne la classe CSS pour un statut"""
#         mapping = {
#             'planned': 'primary',
#             'in_progress': 'warning',
#             'completed': 'success',
#             'cancelled': 'secondary'
#         }
#         return mapping.get(status, 'secondary')

# if __name__ == '__main__':
#     # Initialiser la base de données
#     db = Database()
#     print("Base de données initialisée avec succès!")
#     print("Utilisateur par défaut créé: admin / admin123")

# """
# Gestion de la base de données avec méthodes corrigées
# """
# import sqlite3
# import os
# from datetime import datetime, timedelta
# from typing import List, Dict, Optional

# class Database:
#     def __init__(self, db_path: str = 'data/fertigation.db'):
#         self.db_path = db_path
#         self.ensure_db_exists()
    
#     def ensure_db_exists(self):
#         """S'assure que la base de données existe"""
#         if not os.path.exists(os.path.dirname(self.db_path)):
#             os.makedirs(os.path.dirname(self.db_path))
    
#     def get_connection(self):
#         """Retourne une connexion à la base de données"""
#         conn = sqlite3.connect(self.db_path)
#         conn.row_factory = sqlite3.Row
#         return conn
    
#     def get_recent_readings(self, sensor_name: str, limit: int = 10) -> List[Dict]:
#         """Récupère les lectures récentes d'un capteur"""
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                 SELECT * FROM sensor_readings 
#                 WHERE sensor_name = ? 
#                 ORDER BY timestamp DESC 
#                 LIMIT ?
#             ''', (sensor_name, limit))
            
#             return [dict(row) for row in cursor.fetchall()]
    
#     def get_active_alerts(self, limit: int = None) -> List[Dict]:
#         """Récupère les alertes actives"""
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
            
#             query = '''
#                 SELECT * FROM alerts 
#                 WHERE is_active = 1 
#                 ORDER BY created_at DESC
#             '''
            
#             if limit:
#                 query += f' LIMIT {limit}'
            
#             cursor.execute(query)
            
#             alerts = []
#             for row in cursor.fetchall():
#                 alert = dict(row)
#                 # Ajouter des classes CSS pour l'affichage
#                 alert['severity_class'] = self._get_severity_class(alert['severity'])
#                 alert['severity_text'] = alert['severity'].upper()
#                 alerts.append(alert)
            
#             return alerts
    
#     def get_resolved_alerts(self, limit: int = None) -> List[Dict]:
#         """Récupère les alertes résolues"""
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
            
#             query = '''
#                 SELECT * FROM alerts 
#                 WHERE is_active = 0 
#                 ORDER BY resolved_at DESC
#             '''
            
#             if limit:
#                 query += f' LIMIT {limit}'
            
#             cursor.execute(query)
            
#             alerts = []
#             for row in cursor.fetchall():
#                 alert = dict(row)
#                 alert['severity_class'] = 'resolved'
#                 alert['severity_text'] = 'RÉSOLU'
#                 alerts.append(alert)
            
#             return alerts
    
#     def resolve_alert(self, alert_id: int):
#         """Résout une alerte"""
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                 UPDATE alerts 
#                 SET is_active = 0, resolved_at = ? 
#                 WHERE id = ?
#             ''', (datetime.now(), alert_id))
#             conn.commit()
    
#     def get_latest_predictions(self) -> List[Dict]:
#         """Récupère les dernières prédictions"""
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                 SELECT * FROM predictions 
#                 ORDER BY created_at DESC 
#                 LIMIT 20
#             ''')
            
#             predictions = []
#             for row in cursor.fetchall():
#                 prediction = dict(row)
#                 # Ajouter des informations calculées
#                 prediction['risk_level'] = self._get_risk_level(prediction['failure_probability'])
#                 prediction['risk_class'] = self._get_risk_class(prediction['failure_probability'])
                
#                 # Calculer les jours restants
#                 if prediction['predicted_failure_date']:
#                     failure_date = datetime.fromisoformat(prediction['predicted_failure_date'])
#                     days_left = (failure_date - datetime.now()).days
#                     prediction['days_until_failure'] = max(0, days_left)
#                 else:
#                     prediction['days_until_failure'] = None
                
#                 predictions.append(prediction)
            
#             return predictions
    
#     def get_maintenance_records(self, status: str = None, limit: int = None) -> List[Dict]:
#         """Récupère les enregistrements de maintenance"""
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
            
#             if status:
#                 query = 'SELECT * FROM maintenance_records WHERE status = ? ORDER BY scheduled_date DESC'
#                 params = (status,)
#             else:
#                 query = 'SELECT * FROM maintenance_records ORDER BY scheduled_date DESC'
#                 params = ()
            
#             if limit:
#                 query += f' LIMIT {limit}'
            
#             cursor.execute(query, params)
            
#             records = []
#             for row in cursor.fetchall():
#                 record = dict(row)
#                 record['status_class'] = self._get_status_class(record['status'])
#                 records.append(record)
            
#             return records
    
#     def get_readings_by_timerange(self, start_time: datetime, end_time: datetime, sensor_name: str) -> List[Dict]:
#         """Récupère les lectures dans une plage de temps"""
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                 SELECT * FROM sensor_readings 
#                 WHERE sensor_name = ? AND timestamp BETWEEN ? AND ?
#                 ORDER BY timestamp ASC
#             ''', (sensor_name, start_time, end_time))
            
#             return [dict(row) for row in cursor.fetchall()]
    
#     def insert_sensor_reading(self, sensor_type: str, sensor_name: str, value: float, unit: str):
#         """Insère une nouvelle lecture de capteur"""
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                 INSERT INTO sensor_readings (sensor_type, sensor_name, value, unit, timestamp)
#                 VALUES (?, ?, ?, ?, ?)
#             ''', (sensor_type, sensor_name, value, unit, datetime.now()))
#             conn.commit()
    
#     def create_alert(self, sensor_name: str, alert_type: str, message: str, severity: str) -> int:
#         """Crée une nouvelle alerte"""
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                 INSERT INTO alerts (sensor_name, alert_type, message, severity, is_active, created_at)
#                 VALUES (?, ?, ?, ?, 1, ?)
#             ''', (sensor_name, alert_type, message, severity, datetime.now()))
#             conn.commit()
#             return cursor.lastrowid
    
#     def _get_severity_class(self, severity: str) -> str:
#         """Retourne la classe CSS pour une sévérité"""
#         mapping = {
#             'low': 'info',
#             'medium': 'warning', 
#             'high': 'danger',
#             'critical': 'dark'
#         }
#         return mapping.get(severity.lower(), 'info')
    
#     def _get_risk_level(self, probability: float) -> str:
#         """Retourne le niveau de risque"""
#         if probability < 0.3:
#             return 'FAIBLE'
#         elif probability < 0.6:
#             return 'MOYEN'
#         elif probability < 0.8:
#             return 'ÉLEVÉ'
#         else:
#             return 'CRITIQUE'
    
#     def _get_risk_class(self, probability: float) -> str:
#         """Retourne la classe CSS pour le risque"""
#         if probability < 0.3:
#             return 'success'
#         elif probability < 0.6:
#             return 'info'
#         elif probability < 0.8:
#             return 'warning'
#         else:
#             return 'danger'
    
#     def _get_status_class(self, status: str) -> str:
#         """Retourne la classe CSS pour un statut"""
#         mapping = {
#             'planned': 'primary',
#             'in_progress': 'warning',
#             'completed': 'success',
#             'cancelled': 'secondary'
#         }
#         return mapping.get(status, 'secondary')

# """
# Gestion de la base de données SQLite
# """
# import sqlite3
# import hashlib
# from datetime import datetime
# from config import Config

# class Database:
#     def __init__(self, db_path=None):
#         self.db_path = db_path or Config.DATABASE_PATH
#         self.init_database()
    
#     def get_connection(self):
#         """Obtient une connexion à la base de données"""
#         conn = sqlite3.connect(self.db_path)
#         conn.row_factory = sqlite3.Row
#         return conn
    
#     def init_database(self):
#         """Initialise la base de données avec les tables nécessaires"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         # Table des utilisateurs
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS users (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 username TEXT UNIQUE NOT NULL,
#                 email TEXT UNIQUE NOT NULL,
#                 password_hash TEXT NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         # Table des données de capteurs
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS sensor_readings (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 sensor_type TEXT NOT NULL,
#                 sensor_name TEXT NOT NULL,
#                 value REAL NOT NULL,
#                 unit TEXT NOT NULL,
#                 timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         # Table des alertes
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS alerts (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 sensor_name TEXT NOT NULL,
#                 alert_type TEXT NOT NULL,
#                 message TEXT NOT NULL,
#                 severity INTEGER NOT NULL,
#                 is_active BOOLEAN DEFAULT TRUE,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 resolved_at TIMESTAMP
#             )
#         ''')
        
#         # Table des maintenances
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS maintenance_records (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 sensor_name TEXT NOT NULL,
#                 maintenance_type TEXT NOT NULL,
#                 description TEXT,
#                 scheduled_date TIMESTAMP,
#                 completed_date TIMESTAMP,
#                 status TEXT DEFAULT 'planned'
#             )
#         ''')
        
#         # Table des prédictions
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS predictions (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 sensor_name TEXT NOT NULL,
#                 failure_probability REAL NOT NULL,
#                 predicted_failure_date TIMESTAMP,
#                 confidence_score REAL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         conn.commit()
#         conn.close()
        
#         # Créer un utilisateur admin par défaut
#         self.create_default_user()
    
#     def create_default_user(self):
#         """Crée un utilisateur admin par défaut"""
#         try:
#             password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
#             conn = self.get_connection()
#             cursor = conn.cursor()
#             cursor.execute('''
#                 INSERT OR IGNORE INTO users (username, email, password_hash)
#                 VALUES (?, ?, ?)
#             ''', ('admin', 'admin@fertigation.com', password_hash))
#             conn.commit()
#             conn.close()
#         except Exception as e:
#             print(f"Erreur lors de la création de l'utilisateur par défaut: {e}")
    
#     # Méthodes pour les utilisateurs
#     def get_user_by_username(self, username):
#         """Récupère un utilisateur par son nom d'utilisateur"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
#         user = cursor.fetchone()
#         conn.close()
#         return user
    
#     def get_user_by_id(self, user_id):
#         """Récupère un utilisateur par son ID"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
#         user = cursor.fetchone()
#         conn.close()
#         return user
    
#     def create_user(self, username, email, password):
#         """Crée un nouveau utilisateur"""
#         password_hash = hashlib.sha256(password.encode()).hexdigest()
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         try:
#             cursor.execute('''
#                 INSERT INTO users (username, email, password_hash)
#                 VALUES (?, ?, ?)
#             ''', (username, email, password_hash))
#             conn.commit()
#             return True
#         except sqlite3.IntegrityError:
#             return False
#         finally:
#             conn.close()
    
#     # Méthodes pour les données de capteurs
#     def insert_sensor_reading(self, sensor_type, sensor_name, value, unit):
#         """Insère une nouvelle lecture de capteur"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT INTO sensor_readings (sensor_type, sensor_name, value, unit)
#             VALUES (?, ?, ?, ?)
#         ''', (sensor_type, sensor_name, value, unit))
#         conn.commit()
#         conn.close()
    
#     def get_recent_readings(self, sensor_name=None, limit=100):
#         """Récupère les lectures récentes"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         if sensor_name:
#             cursor.execute('''
#                 SELECT * FROM sensor_readings 
#                 WHERE sensor_name = ? 
#                 ORDER BY timestamp DESC 
#                 LIMIT ?
#             ''', (sensor_name, limit))
#         else:
#             cursor.execute('''
#                 SELECT * FROM sensor_readings 
#                 ORDER BY timestamp DESC 
#                 LIMIT ?
#             ''', (limit,))
        
#         readings = cursor.fetchall()
#         conn.close()
#         return readings
    
#     def get_readings_by_timerange(self, start_time, end_time, sensor_name=None):
#         """Récupère les lectures dans une plage de temps"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         if sensor_name:
#             cursor.execute('''
#                 SELECT * FROM sensor_readings 
#                 WHERE sensor_name = ? AND timestamp BETWEEN ? AND ?
#                 ORDER BY timestamp ASC
#             ''', (sensor_name, start_time, end_time))
#         else:
#             cursor.execute('''
#                 SELECT * FROM sensor_readings 
#                 WHERE timestamp BETWEEN ? AND ?
#                 ORDER BY timestamp ASC
#             ''', (start_time, end_time))
        
#         readings = cursor.fetchall()
#         conn.close()
#         return readings
    
#     # Méthodes pour les alertes
#     def create_alert(self, sensor_name, alert_type, message, severity):
#         """Crée une nouvelle alerte"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT INTO alerts (sensor_name, alert_type, message, severity)
#             VALUES (?, ?, ?, ?)
#         ''', (sensor_name, alert_type, message, severity))
#         alert_id = cursor.lastrowid
#         conn.commit()
#         conn.close()
#         return alert_id
    
#     def get_active_alerts(self):
#         """Récupère les alertes actives"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             SELECT * FROM alerts 
#             WHERE is_active = TRUE 
#             ORDER BY severity DESC, created_at DESC
#         ''')
#         alerts = cursor.fetchall()
#         conn.close()
#         return alerts
    
#     def get_all_alerts(self, limit=200):
#         """Récupère toutes les alertes"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             SELECT * FROM alerts 
#             ORDER BY created_at DESC 
#             LIMIT ?
#         ''', (limit,))
#         alerts = cursor.fetchall()
#         conn.close()
#         return alerts
    
#     def resolve_alert(self, alert_id):
#         """Marque une alerte comme résolue"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             UPDATE alerts 
#             SET is_active = FALSE, resolved_at = CURRENT_TIMESTAMP 
#             WHERE id = ?
#         ''', (alert_id,))
#         conn.commit()
#         conn.close()
    
#     # Méthodes pour la maintenance
#     def create_maintenance_record(self, sensor_name, maintenance_type, description, scheduled_date):
#         """Crée un enregistrement de maintenance"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT INTO maintenance_records 
#             (sensor_name, maintenance_type, description, scheduled_date)
#             VALUES (?, ?, ?, ?)
#         ''', (sensor_name, maintenance_type, description, scheduled_date))
#         maintenance_id = cursor.lastrowid
#         conn.commit()
#         conn.close()
#         return maintenance_id
    
#     def get_maintenance_records(self, status=None):
#         """Récupère les enregistrements de maintenance"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         if status:
#             cursor.execute('''
#                 SELECT * FROM maintenance_records 
#                 WHERE status = ? 
#                 ORDER BY scheduled_date DESC
#             ''', (status,))
#         else:
#             cursor.execute('''
#                 SELECT * FROM maintenance_records 
#                 ORDER BY scheduled_date DESC
#             ''')
        
#         records = cursor.fetchall()
#         conn.close()
#         return records
    
#     def update_maintenance_status(self, maintenance_id, status, completed_date=None):
#         """Met à jour le statut d'une maintenance"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
        
#         if completed_date:
#             cursor.execute('''
#                 UPDATE maintenance_records 
#                 SET status = ?, completed_date = ? 
#                 WHERE id = ?
#             ''', (status, completed_date, maintenance_id))
#         else:
#             cursor.execute('''
#                 UPDATE maintenance_records 
#                 SET status = ? 
#                 WHERE id = ?
#             ''', (status, maintenance_id))
        
#         conn.commit()
#         conn.close()
    
#     # Méthodes pour les prédictions
#     def save_prediction(self, sensor_name, failure_probability, predicted_failure_date, confidence_score):
#         """Sauvegarde une prÃ©diction"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT INTO predictions 
#             (sensor_name, failure_probability, predicted_failure_date, confidence_score)
#             VALUES (?, ?, ?, ?)
#         ''', (sensor_name, failure_probability, predicted_failure_date, confidence_score))
#         prediction_id = cursor.lastrowid
#         conn.commit()
#         conn.close()
#         return prediction_id
    
#     def get_latest_predictions(self):
#         """Récupère les dernières prédictions pour chaque capteur"""
#         conn = self.get_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             SELECT p1.* FROM predictions p1
#             INNER JOIN (
#                 SELECT sensor_name, MAX(created_at) as max_date
#                 FROM predictions
#                 GROUP BY sensor_name
#             ) p2 ON p1.sensor_name = p2.sensor_name AND p1.created_at = p2.max_date
#         ''')
#         predictions = cursor.fetchall()
#         conn.close()
#         return predictions

# if __name__ == '__main__':
#     # Initialiser la base de données
#     db = Database()
#     print("Base de données initialisée avec succès!")
#     print("Utilisateur par défaut créé: admin / admin123")