"""
Script pour nettoyer la base de données
Supprime les anciennes données et alertes
"""
import sqlite3
from datetime import datetime, timedelta
import os

def cleanup_database():
    """Nettoie la base de données"""
    db_path = 'data/fertigation.db'
    
    if not os.path.exists(db_path):
        print("❌ Base de données non trouvée!")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🧹 Nettoyage de la base de données...")
        
        # Compter les données avant nettoyage
        cursor.execute("SELECT COUNT(*) FROM alerts")
        alerts_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        readings_count = cursor.fetchone()[0]
        
        print(f"📊 Avant nettoyage:")
        print(f"   - Alertes: {alerts_count}")
        print(f"   - Lectures capteurs: {readings_count}")
        
        # Supprimer toutes les alertes
        cursor.execute("DELETE FROM alerts")
        print("✅ Toutes les alertes supprimées")
        
        # Garder seulement les données des 7 derniers jours
        seven_days_ago = datetime.now() - timedelta(days=7)
        cursor.execute("DELETE FROM sensor_readings WHERE timestamp < ?", (seven_days_ago,))
        print("✅ Anciennes données de capteurs supprimées (> 7 jours)")
        
        # Supprimer les anciennes prédictions
        cursor.execute("DELETE FROM predictions WHERE created_at < ?", (seven_days_ago,))
        print("✅ Anciennes prédictions supprimées")
        
        # Supprimer les maintenances terminées anciennes
        cursor.execute("DELETE FROM maintenance_records WHERE status = 'completed' AND completed_date < ?", (seven_days_ago,))
        print("✅ Anciennes maintenances supprimées")
        
        # Réinitialiser les compteurs auto-increment
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('alerts', 'sensor_readings', 'predictions', 'maintenance_records')")
        print("✅ Compteurs réinitialisés")
        
        # Compter après nettoyage
        cursor.execute("SELECT COUNT(*) FROM alerts")
        alerts_count_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        readings_count_after = cursor.fetchone()[0]
        
        print(f"📊 Après nettoyage:")
        print(f"   - Alertes: {alerts_count_after}")
        print(f"   - Lectures capteurs: {readings_count_after}")
        
        # Optimiser la base de données
        cursor.execute("VACUUM")
        print("✅ Base de données optimisée")
        
        conn.commit()
        conn.close()
        
        print("🎉 Nettoyage terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")

if __name__ == '__main__':
    print("🧹 === Nettoyage de la base de données ===")
    print("⚠️  ATTENTION: Cette opération va supprimer des données!")
    print("   - Toutes les alertes")
    print("   - Données de capteurs > 7 jours")
    print("   - Prédictions > 7 jours")
    print("   - Maintenances terminées > 7 jours")
    print()
    
    response = input("Voulez-vous continuer? (oui/non): ").lower().strip()
    
    if response in ['oui', 'o', 'yes', 'y']:
        cleanup_database()
    else:
        print("❌ Nettoyage annulé")
