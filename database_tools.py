"""
Outils pour la gestion de la base de données
"""
import sqlite3
from datetime import datetime, timedelta
import os

class DatabaseTools:
    def __init__(self, db_path='data/fertigation.db'):
        self.db_path = db_path
    
    def get_database_stats(self):
        """Récupère les statistiques de la base de données"""
        if not os.path.exists(self.db_path):
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Compter les alertes
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'active'")
            stats['active_alerts'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'resolved'")
            stats['resolved_alerts'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM alerts")
            stats['total_alerts'] = cursor.fetchone()[0]
            
            # Compter les lectures de capteurs
            cursor.execute("SELECT COUNT(*) FROM sensor_readings")
            stats['total_readings'] = cursor.fetchone()[0]
            
            # Lectures par jour (7 derniers jours)
            seven_days_ago = datetime.now() - timedelta(days=7)
            cursor.execute("SELECT COUNT(*) FROM sensor_readings WHERE timestamp >= ?", (seven_days_ago,))
            stats['recent_readings'] = cursor.fetchone()[0]
            
            # Prédictions
            cursor.execute("SELECT COUNT(*) FROM predictions")
            stats['total_predictions'] = cursor.fetchone()[0]
            
            # Maintenances
            cursor.execute("SELECT COUNT(*) FROM maintenance_records WHERE status = 'planned'")
            stats['planned_maintenance'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM maintenance_records WHERE status = 'completed'")
            stats['completed_maintenance'] = cursor.fetchone()[0]
            
            # Taille de la base de données
            stats['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)
            
            conn.close()
            return stats
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des statistiques: {e}")
            return None
    
    def cleanup_old_data(self, days_to_keep=7):
        """Supprime les anciennes données"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Supprimer les anciennes lectures
            cursor.execute("DELETE FROM sensor_readings WHERE timestamp &lt; ?", (cutoff_date,))
            readings_deleted = cursor.rowcount
            
            # Supprimer les anciennes prédictions
            cursor.execute("DELETE FROM predictions WHERE created_at &lt; ?", (cutoff_date,))
            predictions_deleted = cursor.rowcount
            
            # Supprimer les maintenances terminées anciennes
            cursor.execute("DELETE FROM maintenance_records WHERE status = 'completed' AND completed_date &lt; ?", (cutoff_date,))
            maintenance_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            return {
                'readings_deleted': readings_deleted,
                'predictions_deleted': predictions_deleted,
                'maintenance_deleted': maintenance_deleted
            }
            
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage: {e}")
            return None
    
    def clear_all_alerts(self):
        """Supprime toutes les alertes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM alerts")
            alerts_deleted = cursor.rowcount
            
            # Réinitialiser le compteur
            cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'alerts'")
            
            conn.commit()
            conn.close()
            
            return alerts_deleted
            
        except Exception as e:
            print(f"❌ Erreur lors de la suppression des alertes: {e}")
            return None
    
    def backup_database(self, backup_path=None):
        """Crée une sauvegarde de la base de données"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backup_fertigation_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return None

def main():
    """Interface en ligne de commande pour les outils de base de données"""
    tools = DatabaseTools()
    
    while True:
        print("\n🛠️  === Outils de gestion de la base de données ===")
        print("1. Afficher les statistiques")
        print("2. Nettoyer les anciennes données")
        print("3. Supprimer toutes les alertes")
        print("4. Créer une sauvegarde")
        print("5. Quitter")
        
        choice = input("\nChoisissez une option (1-5): ").strip()
        
        if choice == '1':
            stats = tools.get_database_stats()
            if stats:
                print("\n📊 Statistiques de la base de données:")
                print(f"   - Alertes actives: {stats['active_alerts']}")
                print(f"   - Alertes résolues: {stats['resolved_alerts']}")
                print(f"   - Total alertes: {stats['total_alerts']}")
                print(f"   - Lectures totales: {stats['total_readings']}")
                print(f"   - Lectures récentes (7j): {stats['recent_readings']}")
                print(f"   - Prédictions: {stats['total_predictions']}")
                print(f"   - Maintenances planifiées: {stats['planned_maintenance']}")
                print(f"   - Maintenances terminées: {stats['completed_maintenance']}")
                print(f"   - Taille DB: {stats['db_size_mb']:.2f} MB")
            else:
                print("❌ Impossible de récupérer les statistiques")
        
        elif choice == '2':
            days = input("Nombre de jours à conserver (défaut: 7): ").strip()
            days = int(days) if days.isdigit() else 7
            
            result = tools.cleanup_old_data(days)
            if result:
                print(f"✅ Nettoyage terminé:")
                print(f"   - Lectures supprimées: {result['readings_deleted']}")
                print(f"   - Prédictions supprimées: {result['predictions_deleted']}")
                print(f"   - Maintenances supprimées: {result['maintenance_deleted']}")
            else:
                print("❌ Erreur lors du nettoyage")
        
        elif choice == '3':
            confirm = input("⚠️  Supprimer TOUTES les alertes? (oui/non): ").lower().strip()
            if confirm in ['oui', 'o', 'yes', 'y']:
                deleted = tools.clear_all_alerts()
                if deleted is not None:
                    print(f"✅ {deleted} alertes supprimées")
                else:
                    print("❌ Erreur lors de la suppression")
            else:
                print("❌ Suppression annulée")
        
        elif choice == '4':
            backup_path = tools.backup_database()
            if backup_path:
                print(f"✅ Sauvegarde créée: {backup_path}")
            else:
                print("❌ Erreur lors de la sauvegarde")
        
        elif choice == '5':
            print("👋 Au revoir!")
            break
        
        else:
            print("❌ Option invalide")

if __name__ == '__main__':
    main()
