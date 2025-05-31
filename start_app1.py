"""
Script de démarrage simple pour FertiSmart
"""
import os
import sys
from hhch1 import app, socketio, mqtt_client

def start_application():
    """Démarre l'application FertiSmart"""
    print("=== Démarrage de FertiSmart ===")
    
    # Vérifier si la base de données existe
    if not os.path.exists('data/fertigation.db'):
        print("ERREUR: Base de données non trouvée!")
        print("Exécutez d'abord: python init_db.py")
        sys.exit(1)
    
    # Démarrer la connexion MQTT et la simulation
    print("Initialisation du client MQTT...")
    mqtt_client.connect()
    mqtt_client.start_simulation()
    
    print("=== FertiSmart démarré avec succès ===")
    print("🌐 Application web : http://localhost:5000")
    print("👤 Utilisateur : admin")
    print("🔑 Mot de passe : admin123")
    print("=====================================")
    print("Appuyez sur Ctrl+C pour arrêter")
    
    # Démarrer le serveur
    try:
        socketio.run(app, host='127.0.0.1', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n=== Arrêt de FertiSmart ===")
        mqtt_client.disconnect()
        print("Application fermée proprement.")

if __name__ == '__main__':
    start_application()
