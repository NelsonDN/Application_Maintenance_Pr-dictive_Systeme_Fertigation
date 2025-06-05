"""
Script de démarrage pour l'application HTTP
"""
import os
import sys
import signal
import time

def signal_handler(sig, frame):
    """Gestionnaire pour arrêt propre"""
    print('\n🛑 Arrêt de l\'application...')
    sys.exit(0)

def start_application():
    """Démarre l'application"""
    
    # Gestionnaire de signal pour Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🌱 === Cassie's Predictive Tool - Version HTTP ===")
    print()
    
    # Vérifier la base de données
    if not os.path.exists('data/fertigation.db'):
        print("❌ ERREUR: Base de données non trouvée!")
        print("📋 Exécutez d'abord: python init_db.py")
        sys.exit(1)
    
    print("✅ Base de données trouvée")
    
    # Créer l'application
    print("🔧 Initialisation de l'application...")
    from hhch import app, socketio
    # from hhch_esp32 import app, socketio
    
    print()
    print("=== Application démarrée avec succès ===")
    print("🌐 Application web : http://localhost:5000")
    print("👤 Utilisateur : admin")
    print("🔑 Mot de passe : admin123")
    print("📡 Communication : HTTP POST")
    print("🎯 Endpoint ESP32 : /api/sensor_data")
    print("=====================================")
    print("💡 Appuyez sur Ctrl+C pour arrêter")
    print()
    
    try:
        # Démarrer le serveur
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            use_reloader=False,
            log_output=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    finally:
        print("👋 Application fermée proprement.")

if __name__ == '__main__':
    start_application()
