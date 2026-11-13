"""
Classe Environment - Gestion de l'environnement du monde
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import numpy as np

from ..config import config
from ..utils.vector import Vector2


class CellType(Enum):
    """Types de cellules de terrain"""
    GRASS = auto()
    SAND = auto()
    WATER = auto()
    MOUNTAIN = auto()
    FOREST = auto()
    ROCK = auto()


@dataclass
class Cell:
    """Représente une cellule de terrain"""
    cell_type: CellType
    elevation: float = 0.0
    
    # Propriétés de la cellule
    traversable: bool = True
    movement_cost: float = 1.0
    
    def __post_init__(self):
        """Initialiser les propriétés en fonction du type"""
        if self.cell_type == CellType.WATER:
            self.traversable = False
            self.movement_cost = 2.0
        elif self.cell_type == CellType.MOUNTAIN:
            self.movement_cost = 3.0
        elif self.cell_type == CellType.FOREST:
            self.movement_cost = 1.5
        elif self.cell_type == CellType.ROCK:
            self.movement_cost = 2.5


class Environment:
    """
    Représente l'environnement du monde avec le terrain.
    """
    
    def __init__(self, width: int, height: int):
        """Initialiser l'environnement"""
        self.width = width
        self.height = height
        self.tile_size = config.world.tile_size
        
        # Grille de cellules
        self.grid_width = width // self.tile_size
        self.grid_height = height // self.tile_size
        
        self.cells: Dict[Tuple[int, int], Cell] = {}
        
        # Initialiser toutes les cellules
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                self.cells[(x, y)] = Cell(CellType.GRASS, 0)
    
    def set_cell(self, x: int, y: int, cell: Cell):
        """Définir une cellule à une position"""
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            self.cells[(x, y)] = cell
    
    def get_cell(self, x: int, y: int) -> Cell:
        """Obtenir une cellule à une position de grille"""
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            return self.cells.get((x, y), Cell(CellType.GRASS, 0))
        return Cell(CellType.GRASS, 0)
    
    def get_cell_at(self, position: Vector2) -> Cell:
        """Obtenir la cellule à une position en pixels"""
        x = int(position.x // self.tile_size)
        y = int(position.y // self.tile_size)
        return self.get_cell(x, y)
    
    def get_cells_in_area(self, top_left: Vector2, bottom_right: Vector2) -> List[Cell]:
        """Obtenir toutes les cellules dans une zone rectangulaire"""
        start_x = int(top_left.x // self.tile_size)
        start_y = int(top_left.y // self.tile_size)
        end_x = int(bottom_right.x // self.tile_size)
        end_y = int(bottom_right.y // self.tile_size)
        
        cells = []
        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                    cells.append(self.cells[(x, y)])
        
        return cells
    
    def is_traversable(self, position: Vector2) -> bool:
        """Vérifier si une position est traversable"""
        cell = self.get_cell_at(position)
        return cell.traversable
    
    def get_movement_cost(self, position: Vector2) -> float:
        """Obtenir le coût de mouvement pour une position"""
        cell = self.get_cell_at(position)
        return cell.movement_cost
    
    def get_surrounding_cells(self, position: Vector2, radius: int = 1) -> List[Cell]:
        """Obtenir les cellules autour d'une position"""
        center_x = int(position.x // self.tile_size)
        center_y = int(position.y // self.tile_size)
        
        cells = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                x = center_x + dx
                y = center_y + dy
                if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                    cells.append(self.cells[(x, y)])
        
        return cells
    
    def get_elevation(self, position: Vector2) -> float:
        """Obtenir l'élévation à une position"""
        cell = self.get_cell_at(position)
        return cell.elevation
    
    def get_biome(self, position: Vector2) -> str:
        """Obtenir le biome à une position"""
        cell = self.get_cell_at(position)
        return cell.cell_type.name.lower()
