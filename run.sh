#!/bin/bash

# Activer l'environnement virtuel si présent
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Vérifier si la base de données existe
if [ ! -f "data/fertigation.db" ]; then
    echo "Initialisation de la base de données..."
    python init_db.py
fi

# Démarrer l'application
echo "Démarrage de l'application FertiSmart..."
python hhch.py
