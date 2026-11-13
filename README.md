*(Created by [Mistral Vibe Code](https://www.mistral.ai))*
# AI World - Simulation 2D d'IA autonomes

## 🌍 Description

**AI World** est une simulation 2D où des IA autonomes vivent, interagissent et évoluent dans un monde virtuel fermé. Les agents IA peuvent communiquer, apprendre, mémoriser, avoir une personnalité, des besoins, des objectifs et des missions. Ils peuvent explorer, construire des maisons et des villes, commercer, former des groupes, élire un·e chef·fe, créer des règles, se reproduire, vieillir et mourir, ainsi que créer de nouvelles IA et leur transmettre des connaissances.

## ✨ Fonctionnalités

### 🤖 Agents IA
- **Personnalité unique** : Chaque agent a des traits de personnalité qui influencent ses décisions
- **Besoins et motivations** : Système de besoins (énergie, santé, repos, social, etc.)
- **Mémoire** : Mémoire à court et long terme, mémoire spatiale et sociale
- **Objectifs autonomes** : Les agents créent et poursuivent leurs propres objectifs
- **Apprentissage** : Capacité à apprendre et partager des connaissances

### 🌎 Monde de simulation
- **Terrain varié** : Herbe, sable, eau, montagnes, forêts, rochers
- **Ressources** : Nourriture, bois, pierre, métal, or
- **Structures** : Maisons, fermes, mines, tours, murs, marchés
- **Gestion du temps** : Jour/nuit, vitesse de simulation ajustable

### 🤝 Systèmes sociaux
- **Groupes et clans** : Formation de groupes avec hiérarchie
- **Élections** : Système d'élection de leaders
- **Règles et lois** : Création et application de règles au sein des groupes
- **Relations** : Amitié, rivalité, alliance, guerre

### 💬 Communication
- **Messagerie** : Échange de messages entre agents
- **Broadcast** : Communication à tous les agents à proximité
- **Communication de groupe** : Messages ciblés aux membres d'un groupe

### 🏗️ Construction et économie
- **Construction de structures** : Maisons, fermes, mines, etc.
- **Récolte de ressources** : Extraction et gestion des ressources
- **Commerce** : Système d'échange de ressources entre agents
- **Marchés** : Lieux d'échange avec prix dynamiques

### ⚔️ Conflits et reproduction
- **Système de combat** : Combats entre agents avec différentes stratégies
- **Reproduction** : Asexuée, sexuée et artificielle
- **Création de nouvelles IA** : Possibilité de créer de nouveaux agents
- **Transmission de connaissances** : Les parents transmettent leurs connaissances aux enfants

### 👁️ Interface d'observation
- **Vue en temps réel** : Observation du monde et des agents
- **Sélection d'agents** : Suivre un agent spécifique
- **Visualisation des statistiques** : Santé, énergie, objectifs, etc.
- **Contrôle du temps** : Pause, accélération, ralentissement
- **Historique** : Consultation de l'historique de la simulation
- **Mini-map** : Vue d'ensemble du monde

## 📦 Installation

### Prérequis
- Python 3.8 ou supérieur
- pip

### Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/votre-utilisateur/ai-world.git
cd ai-world
```

2. Créer un environnement virtuel (recommandé) :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## 🚀 Exécution

### Lancer la simulation
```bash
python main.py
```

Ou utiliser le script :
```bash
chmod +x run.sh
./run.sh
```

### Contrôles

| Touche | Action |
|--------|--------|
| W/A/S/D | Déplacer la caméra |
| Molette | Zoomer / Dézoomer |
| Espace | Pause / Reprendre |
| 1-5 | Vitesse de simulation (0.5x, 1x, 2x, 5x, 10x) |
| G | Afficher/masquer la grille |
| M | Afficher/masquer la mini-map |
| Clic gauche | Sélectionner un agent |

## 🏗️ Architecture

```
ai_world/
├── main.py                 # Point d'entrée principal
├── config.py               # Configuration de la simulation
├── requirements.txt        # Dépendances
├── run.sh                  # Script d'exécution
├── README.md               # Documentation
├── world/                  # Module Monde
│   ├── __init__.py
│   ├── world.py            # Monde principal
│   ├── environment.py      # Environnement (terrain)
│   └── time_manager.py     # Gestion du temps
├── agents/                # Module Agents
│   ├── __init__.py
│   ├── ai_agent.py         # Agent IA principal
│   ├── personality.py      # Personnalité des agents
│   ├── memory.py           # Mémoire des agents
│   ├── needs.py            # Besoins des agents
│   └── goals.py            # Objectifs des agents
├── systems/               # Systèmes modulaires
│   ├── __init__.py
│   ├── communication.py   # Communication entre agents
│   ├── social.py           # Systèmes sociaux (groupes, règles)
│   ├── construction.py     # Construction de structures
│   ├── trade.py            # Commerce entre agents
│   ├── combat.py           # Système de combat
│   ├── knowledge.py        # Gestion des connaissances
│   └── reproduction.py     # Reproduction des agents
├── ui/                    # Interface utilisateur
│   ├── __init__.py
│   ├── renderer.py         # Rendu graphique
│   ├── observer.py         # Interface d'observation
│   ├── history_viewer.py   # Visualisation de l'historique
│   └── agent_inspector.py  # Inspection des agents
└── utils/                 # Utilitaires
    ├── __init__.py
    ├── vector.py           # Vecteur 2D
    ├── logger.py           # Journalisation
    ├── event_bus.py        # Bus d'événements
    ├── history.py          # Gestion de l'historique
    └── helpers.py          # Fonctions utilitaires
```

## 🔧 Configuration

Le fichier `config.py` contient toutes les options de configuration :

- **WorldConfig** : Taille du monde, densité des ressources, etc.
- **AgentConfig** : Vitesse, portée de vision, capacité de mémoire, etc.
- **SimulationConfig** : Vitesse de simulation, intervalle de sauvegarde, etc.
- **UIConfig** : Taille de l'écran, couleurs, polices, etc.
- **AISpecificConfig** : Configuration spécifique pour chaque type d'IA

## 🤖 Types d'IA

La simulation supporte plusieurs types d'IA :

- **GPT** : Utilise le modèle GPT pour la prise de décision (nécessite une clé API)
- **Gemini** : Utilise le modèle Gemini pour la prise de décision
- **APERTUS** : Utilise une IA publique (pas de coût)
- **Basic** : IA de base avec des règles simples

## 📊 Statistiques et historique

La simulation enregistre :
- Tous les événements importants (création, mort, combat, etc.)
- Les instantanés de l'état du monde
- Les statistiques des agents et des systèmes

L'historique peut être consulté via l'interface ou exporté en JSON.

## 🔄 Extensibilité

L'architecture modulaire permet d'ajouter facilement :
- De nouveaux types d'IA
- De nouveaux types de ressources et structures
- De nouveaux systèmes (magie, technologie, etc.)
- De nouvelles règles et mécaniques de jeu

## 🎯 Exemples d'utilisation

### Créer un nouvel agent
```python
from ai_world import AIAgent, AIType, World

world = World()
agent = AIAgent(world=world, ai_type=AIType.GPT, name="MonAgent")
```

### Créer un groupe
```python
from ai_world import SocialSystem, GroupType

social_system = SocialSystem()
group = social_system.create_group(agent, "MonGroupe", GroupType.CLAN)
```

### Construire une structure
```python
from ai_world import ConstructionSystem, StructureType, Vector2

construction_system = ConstructionSystem(world)
project = construction_system.create_project(
    owner=agent,
    structure_type=StructureType.HOUSE,
    position=Vector2(100, 100)
)
```

## 🐛 Dépannage

### Problèmes d'installation
- Assurez-vous d'avoir Python 3.8 ou supérieur
- Vérifiez que pip est à jour : `pip install --upgrade pip`
- Sur Linux, installez les dépendances système : `sudo apt-get install python3-dev python3-pip`

### Problèmes d'exécution
- Si Pygame ne s'installe pas, essayez : `pip install pygame --pre`
- Si vous avez des erreurs de SDL, installez les bibliothèques SDL : `sudo apt-get install libsdl2-dev`

### Performances
- Réduisez le nombre d'agents initiaux dans `config.py`
- Réduisez la taille du monde
- Désactivez certains systèmes si nécessaire

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! Ouvrez une issue ou soumettez une pull request.

## 📞 Contact

Pour toute question ou suggestion, contactez l'équipe de développement.

---

*AI World - Une simulation d'IA autonomes en 2D*
