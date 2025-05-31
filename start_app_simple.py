"""
Script de démarrage simplifié pour diagnostiquer les problèmes
"""
import os
import sys

def check_environment():
    """Vérifie l'environnement avant le démarrage"""
    print("🔍 === Vérification de l'environnement ===")
    
    # Vérifier le répertoire de travail
    print(f"📁 Répertoire actuel: {os.getcwd()}")
    
    # Vérifier les fichiers nécessaires
    required_files = [
        'config.py',
        'database.py', 
        'models.py',
        'hhch_fixed.py'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MANQUANT")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Fichiers manquants: {missing_files}")
        return False
    
    # Créer le répertoire data s'il n'existe pas
    if not os.path.exists('data'):
        print("📁 Création du répertoire 'data'...")
        os.makedirs('data')
    else:
        print("✅ Répertoire 'data' existe")
    
    return True

def test_database():
    """Test de la base de données"""
    print("\n🗄️  === Test de la base de données ===")
    try:
        from database import Database
        db = Database()
        print("✅ Base de données initialisée")
        return True
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return False

def test_config():
    """Test de la configuration"""
    print("\n⚙️  === Test de la configuration ===")
    try:
        from config import Config
        print(f"✅ DATABASE_PATH: {Config.DATABASE_PATH}")
        print(f"✅ MQTT_BROKER_HOST: {Config.MQTT_BROKER_HOST}")
        return True
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return False

def start_app():
    """Démarre l'application"""
    print("\n🚀 === Démarrage de l'application ===")
    try:
        from hhch_fixed import create_app
        
        print("✅ Modules importés")
        app, socketio = create_app()
        print("✅ Application créée")
        
        print("\n🎉 === FertiSmart démarré ===")
        print("🌐 http://localhost:5000")
        print("👤 admin / admin123")
        print("===============================")
        
        socketio.run(app, host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        
    except Exception as e:
        print(f"❌ Erreur démarrage: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("🌱 FertiSmart - Démarrage diagnostique")
    print("=" * 50)
    
    # Vérifications
    if not check_environment():
        print("\n❌ Environnement non valide")
        return
    
    if not test_config():
        print("\n❌ Configuration non valide")
        return
        
    if not test_database():
        print("\n❌ Base de données non valide")
        return
    
    print("\n✅ Tous les tests passés!")
    
    # Démarrer l'application
    start_app()

if __name__ == '__main__':
    main()
