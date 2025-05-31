"""
Script de démarrage amélioré pour FertiSmart
"""
import os
import sys
import signal
import time

def signal_handler(sig, frame):
    """Gestionnaire pour arrêt propre"""
    print('\n🛑 Arrêt de CSP...')
    sys.exit(0)

def start_application():
    """Démarre l'application FertiSmart"""
    
    # Gestionnaire de signal pour Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🌱 === Cassie's Predictive Tool - Système de Maintenance Prédictive ===")
    print()
    
    # Vérifier la base de données
    if not os.path.exists('data/fertigation.db'):
        print("❌ ERREUR: Base de données non trouvée!")
        print("📋 Exécutez d'abord: python init_db.py")
        sys.exit(1)
    
    print("✅ Base de données trouvée")
    
    # Créer l'application
    print("🔧 Initialisation de l'application...")
    from hhch_fixed import app, socketio
    
    print()
    print("=== FertiSmart démarré avec succès ===")
    print("Application web : http://localhost:5000")
    print("Utilisateur : admin")
    print("Mot de passe : admin123")
    print("=====================================")
    print("💡 Appuyez sur Ctrl+C pour arrêter")
    print()
    
    try:
        # Démarrer le serveur avec configuration optimisée
        socketio.run(
            app, 
            host='127.0.0.1', 
            port=5000, 
            debug=False,
            use_reloader=False,  # ✅ Évite les doubles démarrages
            log_output=False     # ✅ Réduit les logs WebSocket
        )
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    finally:
        print("👋 Cassie's Predictive Tool fermé proprement.")

if __name__ == '__main__':
    start_application()
