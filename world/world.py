"""
Classe World - Représente le monde de simulation 2D
"""

import random
import noise
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict

from ..config import config
from ..utils.vector import Vector2
from ..utils.logger import Logger
from .environment import Environment, Cell, CellType
from .time_manager import TimeManager


class TerrainType(Enum):
    """Types de terrain"""
    GRASS = auto()
    SAND = auto()
    WATER = auto()
    MOUNTAIN = auto()
    FOREST = auto()
    ROCK = auto()


class ResourceType(Enum):
    """Types de ressources"""
    FOOD = auto()
    WOOD = auto()
    STONE = auto()
    METAL = auto()
    WATER = auto()
    GOLD = auto()


@dataclass
class Resource:
    """Représente une ressource dans le monde"""
    resource_type: ResourceType
    amount: float
    max_amount: float
    position: Vector2
    regrowth_rate: float = 0.01
    
    def harvest(self, amount: float) -> float:
        """Récolter une certaine quantité de ressource"""
        harvested = min(amount, self.amount)
        self.amount -= harvested
        return harvested
    
    def regrow(self):
        """Faire repousser la ressource"""
        if self.amount < self.max_amount:
            self.amount = min(self.amount + self.regrowth_rate, self.max_amount)


@dataclass
class Structure:
    """Représente une structure construite par les agents"""
    structure_id: str
    structure_type: str  # "house", "farm", "mine", "tower", etc.
    position: Vector2
    size: Tuple[int, int]
    owner_id: Optional[str] = None
    group_id: Optional[str] = None
    health: float = 100.0
    max_health: float = 100.0
    
    # Capacités de la structure
    can_store_resources: bool = True
    can_produce: bool = False
    production_type: Optional[ResourceType] = None
    production_rate: float = 0.0
    
    # Stockage
    stored_resources: Dict[ResourceType, float] = field(default_factory=dict)
    max_storage: float = 1000.0
    
    def store_resource(self, resource_type: ResourceType, amount: float) -> float:
        """Stocker une ressource"""
        current = self.stored_resources.get(resource_type, 0)
        space = self.max_storage - sum(self.stored_resources.values())
        stored = min(amount, space)
        self.stored_resources[resource_type] = current + stored
        return stored
    
    def retrieve_resource(self, resource_type: ResourceType, amount: float) -> float:
        """Récupérer une ressource"""
        current = self.stored_resources.get(resource_type, 0)
        retrieved = min(amount, current)
        self.stored_resources[resource_type] = current - retrieved
        if self.stored_resources[resource_type] <= 0:
            del self.stored_resources[resource_type]
        return retrieved
    
    def produce(self):
        """Produire des ressources si possible"""
        if self.can_produce and self.production_type:
            # Vérifier si on a assez d'espace
            current = self.stored_resources.get(self.production_type, 0)
            if sum(self.stored_resources.values()) < self.max_storage:
                produced = self.production_rate
                self.stored_resources[self.production_type] = current + produced
                return produced
        return 0.0


class World:
    """
    Représente le monde de simulation 2D complet.
    Gère le terrain, les ressources, les structures et les interactions spatiales.
    """
    
    def __init__(self, width: int = None, height: int = None):
        """Initialiser le monde"""
        self.width = width or config.world.width
        self.height = height or config.world.height
        self.tile_size = config.world.tile_size
        self.logger = Logger("World")
        
        # Environnement
        self.environment = Environment(self.width, self.height)
        
        # Ressources
        self.resources: Dict[str, Resource] = {}
        self.resource_counter = 0
        
        # Structures
        self.structures: Dict[str, Structure] = {}
        self.structure_counter = 0
        
        # Gestion du temps
        self.time_manager = TimeManager()
        
        # Zones d'intérêt (pour l'optimisation)
        self.regions: Dict[Tuple[int, int], List[str]] = defaultdict(list)
        self.region_size = 500  # Taille des régions en pixels
        
        # Génération initiale
        self._generate_terrain()
        self._generate_resources()
        
        self.logger.info(f"Monde initialisé: {self.width}x{self.height}")
    
    def _generate_terrain(self):
        """Générer le terrain avec du bruit de Perlin"""
        seed = config.world.terrain_seed or random.randint(0, 10000)
        
        # Générer le bruit de base
        scale = 100.0
        octaves = 6
        persistence = 0.5
        lacunarity = 2.0
        
        for x in range(0, self.width, self.tile_size):
            for y in range(0, self.height, self.tile_size):
                # Calculer la valeur de bruit
                value = noise.pnoise2(
                    x / scale,
                    y / scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=self.width,
                    repeaty=self.height,
                    base=seed
                )
                
                # Déterminer le type de cellule
                cell_x, cell_y = x // self.tile_size, y // self.tile_size
                
                if value < -0.3:
                    cell_type = CellType.WATER
                elif value < -0.1:
                    cell_type = CellType.SAND
                elif value < 0.1:
                    cell_type = CellType.GRASS
                elif value < 0.3:
                    cell_type = CellType.FOREST
                elif value < 0.5:
                    cell_type = CellType.ROCK
                else:
                    cell_type = CellType.MOUNTAIN
                
                # Créer la cellule
                self.environment.set_cell(cell_x, cell_y, Cell(cell_type, 0))
    
    def _generate_resources(self):
        """Générer les ressources aléatoirement dans le monde"""
        num_resources = int(
            (self.width * self.height * config.world.resource_density) 
            / (self.tile_size * self.tile_size)
        )
        
        for _ in range(num_resources):
            self._spawn_resource()
    
    def _spawn_resource(self, position: Vector2 = None, resource_type: ResourceType = None) -> Resource:
        """Faire apparaître une nouvelle ressource"""
        if position is None:
            position = Vector2(
                random.randint(50, self.width - 50),
                random.randint(50, self.height - 50)
            )
        
        if resource_type is None:
            # Pondération des types de ressources
            weights = {
                ResourceType.FOOD: 0.4,
                ResourceType.WOOD: 0.3,
                ResourceType.STONE: 0.2,
                ResourceType.METAL: 0.05,
                ResourceType.GOLD: 0.05
            }
            resource_type = random.choices(
                list(weights.keys()),
                weights=list(weights.values()),
                k=1
            )[0]
        
        # Déterminer la quantité en fonction du terrain
        cell = self.environment.get_cell_at(position)
        if cell.cell_type == CellType.FOREST:
            max_amount = random.uniform(50, 150)
        elif cell.cell_type == CellType.MOUNTAIN:
            max_amount = random.uniform(100, 200)
        elif cell.cell_type == CellType.WATER:
            max_amount = random.uniform(30, 100)
        else:
            max_amount = random.uniform(20, 80)
        
        resource = Resource(
            resource_type=resource_type,
            amount=max_amount,
            max_amount=max_amount,
            position=position,
            regrowth_rate=random.uniform(0.005, 0.02)
        )
        
        resource_id = f"resource_{self.resource_counter}"
        self.resource_counter += 1
        self.resources[resource_id] = resource
        
        # Ajouter à la région
        region_x = int(position.x // self.region_size)
        region_y = int(position.y // self.region_size)
        self.regions[(region_x, region_y)].append(resource_id)
        
        return resource
    
    def get_nearby_resources(self, position: Vector2, radius: float) -> List[Resource]:
        """Obtenir les ressources à proximité d'une position"""
        nearby = []
        
        # Calculer la région
        region_x = int(position.x // self.region_size)
        region_y = int(position.y // self.region_size)
        
        # Vérifier les régions adjacentes
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check_region = (region_x + dx, region_y + dy)
                if check_region in self.regions:
                    for resource_id in self.regions[check_region]:
                        resource = self.resources[resource_id]
                        if resource.position.distance_to(position) <= radius:
                            nearby.append(resource)
        
        return nearby
    
    def get_nearby_structures(self, position: Vector2, radius: float) -> List[Structure]:
        """Obtenir les structures à proximité"""
        return [
            s for s in self.structures.values()
            if s.position.distance_to(position) <= radius
        ]
    
    def add_structure(self, structure_type: str, position: Vector2, 
                     size: Tuple[int, int], owner_id: str = None, 
                     group_id: str = None) -> Structure:
        """Ajouter une nouvelle structure"""
        structure = Structure(
            structure_id=f"structure_{self.structure_counter}",
            structure_type=structure_type,
            position=position,
            size=size,
            owner_id=owner_id,
            group_id=group_id
        )
        
        self.structure_counter += 1
        self.structures[structure.structure_id] = structure
        
        # Ajouter à la région
        region_x = int(position.x // self.region_size)
        region_y = int(position.y // self.region_size)
        self.regions[(region_x, region_y)].append(structure.structure_id)
        
        self.logger.info(f"Structure créée: {structure_type} à {position}")
        return structure
    
    def remove_structure(self, structure_id: str):
        """Supprimer une structure"""
        if structure_id in self.structures:
            structure = self.structures[structure_id]
            
            # Retirer de la région
            region_x = int(structure.position.x // self.region_size)
            region_y = int(structure.position.y // self.region_size)
            if (region_x, region_y) in self.regions:
                if structure_id in self.regions[(region_x, region_y)]:
                    self.regions[(region_x, region_y)].remove(structure_id)
            
            del self.structures[structure_id]
            self.logger.info(f"Structure supprimée: {structure_id}")
    
    def update(self, delta_time: float):
        """Mettre à jour le monde"""
        # Faire repousser les ressources
        for resource in self.resources.values():
            resource.regrow()
        
        # Produire dans les structures
        for structure in self.structures.values():
            structure.produce()
        
        # Mettre à jour le gestionnaire de temps
        self.time_manager.update(delta_time)
    
    def get_cell_at(self, position: Vector2) -> Cell:
        """Obtenir la cellule à une position donnée"""
        return self.environment.get_cell_at(position)
    
    def get_path(self, start: Vector2, end: Vector2) -> List[Vector2]:
        """
        Trouver un chemin entre deux points (A* simplifié)
        """
        # Implémentation simplifiée - à améliorer
        # Pour l'instant, retourne une ligne droite
        
        path = []
        steps = max(abs(end.x - start.x), abs(end.y - start.y))
        if steps == 0:
            return [start]
        
        for i in range(int(steps)):
            t = i / steps
            path.append(Vector2(
                start.x + (end.x - start.x) * t,
                start.y + (end.y - start.y) * t
            ))
        
        path.append(end)
        return path
    
    def is_position_valid(self, position: Vector2) -> bool:
        """Vérifier si une position est valide (pas dans l'eau, etc.)"""
        cell = self.get_cell_at(position)
        return cell.cell_type != CellType.WATER
    
    def get_random_spawn_position(self) -> Vector2:
        """Obtenir une position de spawn aléatoire valide"""
        center = Vector2(self.width / 2, self.height / 2)
        
        for _ in range(100):  # Essayer 100 fois
            angle = random.uniform(0, 2 * 3.14159)
            distance = random.uniform(100, config.world.spawn_radius)
            
            position = Vector2(
                center.x + distance * np.cos(angle),
                center.y + distance * np.sin(angle)
            )
            
            if self.is_position_valid(position):
                return position
        
        # Si on n'a pas trouvé, retourner le centre
        return center
    
    def get_stats(self) -> Dict:
        """Obtenir les statistiques du monde"""
        return {
            "total_resources": len(self.resources),
            "total_structures": len(self.structures),
            "time": self.time_manager.get_time_string(),
            "regions": len(self.regions)
        }
