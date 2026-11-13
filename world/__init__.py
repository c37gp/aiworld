"""
Module World - Gestion du monde de simulation 2D
"""

from .world import World, TerrainType, ResourceType
from .environment import Environment, Cell, CellType
from .time_manager import TimeManager

__all__ = [
    "World", 
    "Environment", 
    "Cell", 
    "CellType",
    "TerrainType", 
    "ResourceType",
    "TimeManager"
]
