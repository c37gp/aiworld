#!/bin/bash

# Script pour exécuter la simulation AI World

echo "Démarrage de AI World..."

# Créer un environnement virtuel si nécessaire
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
if [ ! -f "venv/lib/python3.*/site-packages/pygame/__init__.py" ]; then
    echo "Installation des dépendances..."
    pip install -r requirements.txt
fi

# Exécuter la simulation
echo "Lancement de la simulation..."
python main.py

# Désactiver l'environnement virtuel
deactivate
