"""
Configuration principale pour AI World
"""

import pygame
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum


class SimulationMode(Enum):
    """Modes de simulation"""
    REAL_TIME = "real_time"
    FAST = "fast"
    PAUSED = "paused"
    STEP_BY_STEP = "step_by_step"


class AIType(Enum):
    """Types d'IA disponibles"""
    GPT = "GPT"
    GEMINI = "Gemini"
    APERTUS = "Apertus"
    BASIC = "Basic"


@dataclass
class WorldConfig:
    """Configuration du monde"""
    width: int = 2000
    height: int = 1500
    tile_size: int = 20
    background_color: Tuple[int, int, int] = (40, 40, 60)
    grid_color: Tuple[int, int, int] = (60, 60, 80)
    max_agents: int = 100
    initial_agents: int = 10
    spawn_radius: int = 200
    
    # Génération du terrain
    terrain_seed: Optional[int] = None
    mountain_density: float = 0.05
    forest_density: float = 0.2
    water_density: float = 0.1
    resource_density: float = 0.15


@dataclass
class AgentConfig:
    """Configuration des agents IA"""
    size: int = 12
    speed: float = 2.0
    max_speed: float = 4.0
    vision_range: int = 150
    communication_range: int = 200
    memory_capacity: int = 1000
    max_age: int = 1000  # en ticks
    reproduction_age: int = 200
    reproduction_cooldown: int = 500
    
    # Besoins (valeurs initiales)
    initial_energy: float = 100.0
    max_energy: float = 200.0
    energy_decay_rate: float = 0.01
    initial_health: float = 100.0
    max_health: float = 100.0
    
    # Personnalité
    personality_traits: List[str] = field(default_factory=lambda: [
        "curiosity", "aggressiveness", "sociability", 
        "intelligence", "creativity", "loyalty"
    ])


@dataclass
class SimulationConfig:
    """Configuration de la simulation"""
    tick_rate: int = 30  # ticks par seconde
    time_scale: float = 1.0  # échelle de temps
    max_history: int = 10000
    auto_save_interval: int = 300  # sauvegarde tous les 300 ticks
    
    # Probabilités d'événements aléatoires
    random_event_probability: float = 0.01
    disaster_probability: float = 0.001


@dataclass
class UIConfig:
    """Configuration de l'interface utilisateur"""
    screen_width: int = 1200
    screen_height: int = 800
    fps: int = 60
    font_name: str = "Arial"
    font_size: int = 14
    
    # Couleurs UI
    background: Tuple[int, int, int] = (30, 30, 40)
    panel_background: Tuple[int, int, int] = (50, 50, 70)
    text_color: Tuple[int, int, int] = (220, 220, 240)
    highlight_color: Tuple[int, int, int] = (100, 180, 255)
    danger_color: Tuple[int, int, int] = (255, 80, 80)
    success_color: Tuple[int, int, int] = (80, 255, 80)
    
    # Taille des panneaux
    info_panel_width: int = 300
    mini_map_size: int = 200


@dataclass
class AISpecificConfig:
    """Configuration spécifique pour chaque type d'IA"""
    gpt_config: Dict = field(default_factory=lambda: {
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 200,
        "rate_limit": 10,  # requêtes par minute
        "cost_per_request": 0.001
    })
    gemini_config: Dict = field(default_factory=lambda: {
        "model": "gemini-pro",
        "temperature": 0.7,
        "max_tokens": 200,
        "rate_limit": 10,
        "cost_per_request": 0.001
    })
    apertus_config: Dict = field(default_factory=lambda: {
        "model": "public-ai",
        "temperature": 0.7,
        "max_tokens": 200,
        "rate_limit": 20,  # plus élevé pour l'IA publique
        "cost_per_request": 0.0
    })


class Config:
    """Configuration globale"""
    
    def __init__(self):
        self.world = WorldConfig()
        self.agent = AgentConfig()
        self.simulation = SimulationConfig()
        self.ui = UIConfig()
        self.ai_specific = AISpecificConfig()
        
        # Initialisation de Pygame
        pygame.init()
        pygame.display.set_caption("AI World - Simulation")
        
    def get_screen_size(self) -> Tuple[int, int]:
        """Retourne la taille de l'écran"""
        return (self.ui.screen_width, self.ui.screen_height)
    
    def get_world_size(self) -> Tuple[int, int]:
        """Retourne la taille du monde"""
        return (self.world.width, self.world.height)


# Instance globale de configuration
config = Config()


# Chemins des ressources
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
SAVE_DIR = os.path.join(os.path.dirname(__file__), "saves")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

# Créer les dossiers si ils n'existent pas
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
