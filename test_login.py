"""
Script de test pour vérifier le système de connexion
"""
import hashlib
from database import Database
from models import User

def test_password_hash():
    """Test du système de hachage des mots de passe"""
    print("🔐 === Test du système de connexion ===")
    
    # Test du hachage
    password = "admin123"
    expected_hash = hashlib.sha256(password.encode()).hexdigest()
    print(f"🔑 Mot de passe: {password}")
    print(f"🔒 Hash attendu: {expected_hash}")
    
    # Vérifier en base
    db = Database()
    user_data = db.get_user_by_username("admin")
    
    if user_data:
        print(f"👤 Utilisateur trouvé: {user_data['username']}")
        print(f"🔒 Hash en base: {user_data['password_hash']}")
        print(f"✅ Hash correspond: {expected_hash == user_data['password_hash']}")
        
        # Test avec la classe User
        user = User.get_by_username("admin")
        if user:
            print(f"🧪 Test check_password: {user.check_password(password)}")
        else:
            print("❌ Impossible de créer l'objet User")
    else:
        print("❌ Utilisateur admin non trouvé en base")
        
        # Créer l'utilisateur admin
        print("📝 Création de l'utilisateur admin...")
        success = db.create_user("admin", "admin@fertigation.com", "admin123", "admin")
        if success:
            print("✅ Utilisateur admin créé")
        else:
            print("❌ Échec de création de l'utilisateur")

def reset_admin_password():
    """Remet à zéro le mot de passe admin"""
    print("\n🔄 === Réinitialisation du mot de passe admin ===")
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Supprimer l'ancien utilisateur admin
    cursor.execute("DELETE FROM users WHERE username = 'admin'")
    
    # Créer un nouvel utilisateur admin
    password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    ''', ('admin', 'admin@fertigation.com', password_hash, 'admin'))
    
    conn.commit()
    conn.close()
    
    print("✅ Mot de passe admin réinitialisé")
    print("👤 Utilisateur: admin")
    print("🔑 Mot de passe: admin123")

if __name__ == '__main__':
    test_password_hash()
    
    # Si le test échoue, réinitialiser
    response = input("\n❓ Voulez-vous réinitialiser le mot de passe admin ? (o/n): ")
    if response.lower() in ['o', 'oui', 'y', 'yes']:
        reset_admin_password()
        print("\n🧪 Test après réinitialisation:")
        test_password_hash()
