"""
AI World - Simulation 2D d'IA autonomes

Ce package implémente une simulation 2D où des IA autonomes vivent,
interagissent et évoluent dans un monde virtuel fermé.
"""

__version__ = "1.0.0"
__author__ = "AI World Team"

from .config import config, Config, WorldConfig, AgentConfig, SimulationConfig, UIConfig, AIType, SimulationMode

# Exporter les modules principaux
from .world import World, Environment, TerrainType, ResourceType
from .agents import AIAgent, AgentPersonality, AgentState, AgentMemory
from .systems import (
    CommunicationSystem,
    SocialSystem,
    ConstructionSystem,
    TradeSystem,
    CombatSystem,
    KnowledgeSystem,
    ReproductionSystem
)
from .ui import Renderer
from .utils import (
    Vector2,
    Distance,
    Logger,
    EventBus,
    HistoryManager
)

__all__ = [
    # Config
    "config", "Config", "WorldConfig", "AgentConfig", 
    "SimulationConfig", "UIConfig", "AIType", "SimulationMode",
    
    # World
    "World", "Environment", "TerrainType", "ResourceType",
    
    # Agents
    "AIAgent", "AgentPersonality", "AgentState", "AgentMemory",
    
    # Systems
    "CommunicationSystem", "MemorySystem", "NeedSystem", 
    "GoalSystem", "SocialSystem", "ConstructionSystem",
    "TradeSystem", "CombatSystem", "KnowledgeSystem",
    "ReproductionSystem",
    
    # UI
    "Renderer", "ObserverUI", "HistoryViewer", "AgentInspector",
    
    # Utils
    "Vector2", "Distance", "Logger", "EventBus", "HistoryManager"
]
