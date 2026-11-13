"""
Classe ConstructionSystem - Système de construction pour AI World
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from ..config import config
from ..utils.vector import Vector2
from ..utils.logger import Logger
from ..world.world import World, Structure, ResourceType
from ..agents.ai_agent import AIAgent


class StructureType(Enum):
    """Types de structures"""
    HOUSE = auto()
    FARM = auto()
    MINE = auto()
    TOWER = auto()
    WALL = auto()
    MARKET = auto()
    TEMPLE = auto()
    WORKSHOP = auto()
    STORAGE = auto()


@dataclass
class Blueprint:
    """Plan de construction"""
    structure_type: StructureType
    name: str
    size: Tuple[int, int]
    cost: Dict[ResourceType, float]  # Coût en ressources
    build_time: float  # Temps de construction (secondes)
    max_health: float = 100.0
    
    # Capacités
    can_store_resources: bool = False
    max_storage: float = 0.0
    production_type: Optional[ResourceType] = None
    production_rate: float = 0.0
    
    # Bonus
    defense_bonus: float = 0.0
    
    @classmethod
    def get_blueprint(cls, structure_type: StructureType) -> "Blueprint":
        """Obtenir un plan de construction par défaut"""
        blueprints = {
            StructureType.HOUSE: cls(
                structure_type=StructureType.HOUSE,
                name="Maison",
                size=(40, 40),
                cost={ResourceType.WOOD: 50, ResourceType.STONE: 30},
                build_time=10.0,
                max_health=150.0,
                can_store_resources=True,
                max_storage=200.0
            ),
            StructureType.FARM: cls(
                structure_type=StructureType.FARM,
                name="Fermes",
                size=(60, 60),
                cost={ResourceType.WOOD: 80, ResourceType.STONE: 20},
                build_time=15.0,
                max_health=120.0,
                production_type=ResourceType.FOOD,
                production_rate=0.5
            ),
            StructureType.MINE: cls(
                structure_type=StructureType.MINE,
                name="Mine",
                size=(50, 50),
                cost={ResourceType.STONE: 100, ResourceType.METAL: 20},
                build_time=20.0,
                max_health=200.0,
                production_type=ResourceType.METAL,
                production_rate=0.3
            ),
            StructureType.TOWER: cls(
                structure_type=StructureType.TOWER,
                name="Tour",
                size=(30, 30),
                cost={ResourceType.STONE: 150, ResourceType.METAL: 50},
                build_time=30.0,
                max_health=300.0,
                defense_bonus=2.0
            ),
            StructureType.WALL: cls(
                structure_type=StructureType.WALL,
                name="Mur",
                size=(20, 10),
                cost={ResourceType.STONE: 30},
                build_time=5.0,
                max_health=80.0,
                defense_bonus=1.0
            ),
            StructureType.MARKET: cls(
                structure_type=StructureType.MARKET,
                name="Marché",
                size=(50, 50),
                cost={ResourceType.WOOD: 60, ResourceType.STONE: 40},
                build_time=12.0,
                max_health=100.0,
                can_store_resources=True,
                max_storage=500.0
            ),
            StructureType.TEMPLE: cls(
                structure_type=StructureType.TEMPLE,
                name="Temple",
                size=(70, 70),
                cost={ResourceType.STONE: 200, ResourceType.GOLD: 50},
                build_time=40.0,
                max_health=400.0
            ),
            StructureType.WORKSHOP: cls(
                structure_type=StructureType.WORKSHOP,
                name="Atelier",
                size=(45, 45),
                cost={ResourceType.WOOD: 70, ResourceType.METAL: 30},
                build_time=15.0,
                max_health=180.0,
                can_store_resources=True,
                max_storage=300.0
            ),
            StructureType.STORAGE: cls(
                structure_type=StructureType.STORAGE,
                name="Entrepôt",
                size=(80, 80),
                cost={ResourceType.WOOD: 100, ResourceType.STONE: 100},
                build_time=25.0,
                max_health=250.0,
                can_store_resources=True,
                max_storage=1000.0
            )
        }
        
        return blueprints.get(structure_type, blueprints[StructureType.HOUSE])


@dataclass
class ConstructionProject:
    """Projet de construction"""
    project_id: str
    blueprint: Blueprint
    position: Vector2
    owner_id: str
    group_id: Optional[str] = None
    
    # Progression
    progress: float = 0.0  # 0-1
    current_resources: Dict[ResourceType, float] = field(default_factory=dict)
    
    # Travailleurs
    workers: List[str] = field(default_factory=list)  # agent_ids
    max_workers: int = 3
    
    # État
    is_complete: bool = False
    is_cancelled: bool = False
    
    def __post_init__(self):
        for resource_type in self.blueprint.cost:
            self.current_resources[resource_type] = 0.0
    
    def add_worker(self, agent_id: str) -> bool:
        """Ajouter un travailleur"""
        if len(self.workers) >= self.max_workers:
            return False
        if agent_id in self.workers:
            return False
        
        self.workers.append(agent_id)
        return True
    
    def remove_worker(self, agent_id: str) -> bool:
        """Retirer un travailleur"""
        if agent_id in self.workers:
            self.workers.remove(agent_id)
            return True
        return False
    
    def add_resources(self, resource_type: ResourceType, amount: float) -> float:
        """Ajouter des ressources au projet"""
        needed = self.blueprint.cost.get(resource_type, 0)
        current = self.current_resources.get(resource_type, 0)
        
        if current >= needed:
            return 0.0  # On a déjà assez
        
        can_add = min(amount, needed - current)
        self.current_resources[resource_type] = current + can_add
        
        # Mettre à jour la progression
        self._update_progress()
        
        return can_add
    
    def _update_progress(self):
        """Mettre à jour la progression"""
        total_cost = sum(self.blueprint.cost.values())
        if total_cost == 0:
            self.progress = 1.0
            return
        
        total_added = sum(self.current_resources.values())
        self.progress = min(1.0, total_added / total_cost)
        
        if self.progress >= 1.0:
            self.is_complete = True
    
    def update(self, delta_time: float, worker_count: int = 1):
        """Mettre à jour le projet avec le travail des ouvriers"""
        if self.is_complete or self.is_cancelled:
            return
        
        # Calculer la progression basée sur le travail
        work_rate = 0.1 * worker_count  # Taux de travail par ouvrier
        self.progress = min(1.0, self.progress + work_rate * delta_time)
        
        if self.progress >= 1.0:
            self.is_complete = True
    
    def cancel(self):
        """Annuler le projet"""
        self.is_cancelled = True
    
    def get_remaining_resources(self) -> Dict[ResourceType, float]:
        """Obtenir les ressources manquantes"""
        remaining = {}
        for resource_type, needed in self.blueprint.cost.items():
            current = self.current_resources.get(resource_type, 0)
            remaining[resource_type] = max(0, needed - current)
        return remaining
    
    def can_start(self) -> bool:
        """Vérifier si le projet peut commencer (toutes les ressources sont disponibles)"""
        for resource_type, needed in self.blueprint.cost.items():
            if self.current_resources.get(resource_type, 0) < needed:
                return False
        return True


class ConstructionSystem:
    """
    Système de construction pour AI World.
    Gère les projets de construction et les structures.
    """
    
    def __init__(self, world: World):
        """Initialiser le système de construction"""
        self.world = world
        self.logger = Logger("ConstructionSystem")
        
        # Projets de construction
        self.projects: Dict[str, ConstructionProject] = {}
        self.project_counter = 0
        
        # Structures construites
        self.structures: Dict[str, Structure] = {}  # Copie des structures du monde
        
        # Statistiques
        self.stats = {
            "projects_started": 0,
            "projects_completed": 0,
            "projects_cancelled": 0,
            "total_structures": 0
        }
    
    def create_project(self, owner: AIAgent, structure_type: StructureType,
                      position: Vector2, group_id: str = None) -> Optional[ConstructionProject]:
        """Créer un nouveau projet de construction"""
        # Obtenir le plan
        blueprint = Blueprint.get_blueprint(structure_type)
        
        # Vérifier si la position est valide
        if not self.world.is_position_valid(position):
            self.logger.warning(f"Position invalide pour la construction: {position}")
            return None
        
        # Vérifier si une structure existe déjà à cet endroit
        nearby_structures = self.world.get_nearby_structures(position, 50)
        if nearby_structures:
            self.logger.warning(f"Une structure existe déjà à {position}")
            return None
        
        # Créer le projet
        project = ConstructionProject(
            project_id=f"project_{self.project_counter}",
            blueprint=blueprint,
            position=position,
            owner_id=owner.agent_id,
            group_id=group_id
        )
        
        self.project_counter += 1
        self.projects[project.project_id] = project
        
        # Statistiques
        self.stats["projects_started"] += 1
        
        self.logger.info(f"Projet créé: {blueprint.name} à {position}")
        
        return project
    
    def start_project(self, project_id: str, initial_resources: Dict[ResourceType, float] = None) -> bool:
        """Démarrer un projet de construction"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        
        if initial_resources:
            for resource_type, amount in initial_resources.items():
                project.add_resources(resource_type, amount)
        
        # Vérifier si on peut commencer
        if project.can_start():
            project._update_progress()  # Forcer la mise à jour
            self.logger.info(f"Projet démarré: {project.project_id}")
            return True
        
        return True  # On peut démarrer même sans toutes les ressources
    
    def add_worker(self, project_id: str, agent: AIAgent) -> bool:
        """Ajouter un travailleur à un projet"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        
        # Vérifier si l'agent peut travailler sur ce projet
        # (par exemple, doit être dans le même groupe)
        if project.group_id and agent.group_id != project.group_id:
            return False
        
        return project.add_worker(agent.agent_id)
    
    def remove_worker(self, project_id: str, agent: AIAgent) -> bool:
        """Retirer un travailleur d'un projet"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        return project.remove_worker(agent.agent_id)
    
    def add_resources(self, project_id: str, agent: AIAgent, 
                      resource_type: ResourceType, amount: float) -> float:
        """Ajouter des ressources à un projet depuis l'inventaire d'un agent"""
        if project_id not in self.projects:
            return 0.0
        
        project = self.projects[project_id]
        
        # Vérifier si l'agent a la ressource
        available = agent.inventory.get(resource_type, 0)
        transfer_amount = min(amount, available)
        
        if transfer_amount > 0:
            # Retirer de l'agent
            agent.inventory[resource_type] -= transfer_amount
            
            # Ajouter au projet
            added = project.add_resources(resource_type, transfer_amount)
            
            self.logger.debug(f"Ressources ajoutées: {transfer_amount} {resource_type.name} au projet {project_id}")
            
            return added
        
        return 0.0
    
    def update_projects(self, delta_time: float):
        """Mettre à jour tous les projets"""
        completed_projects = []
        
        for project_id, project in self.projects.items():
            if project.is_complete or project.is_cancelled:
                continue
            
            # Mettre à jour avec le nombre de travailleurs
            worker_count = len(project.workers)
            project.update(delta_time, worker_count)
            
            # Vérifier si le projet est complet
            if project.is_complete:
                completed_projects.append(project_id)
        
        # Traiter les projets complétés
        for project_id in completed_projects:
            self._complete_project(project_id)
    
    def _complete_project(self, project_id: str):
        """Compléter un projet et créer la structure"""
        if project_id not in self.projects:
            return
        
        project = self.projects[project_id]
        
        # Créer la structure dans le monde
        structure = self.world.add_structure(
            structure_type=project.blueprint.structure_type.name,
            position=project.position,
            size=project.blueprint.size,
            owner_id=project.owner_id,
            group_id=project.group_id
        )
        
        # Configurer la structure
        structure.max_health = project.blueprint.max_health
        structure.can_store_resources = project.blueprint.can_store_resources
        structure.max_storage = project.blueprint.max_storage
        structure.can_produce = project.blueprint.production_type is not None
        structure.production_type = project.blueprint.production_type
        structure.production_rate = project.blueprint.production_rate
        
        # Enregistrer la structure
        self.structures[structure.structure_id] = structure
        
        # Supprimer le projet
        del self.projects[project_id]
        
        # Statistiques
        self.stats["projects_completed"] += 1
        self.stats["total_structures"] += 1
        
        self.logger.info(f"Projet complété: {project.blueprint.name} à {project.position}")
    
    def cancel_project(self, project_id: str) -> bool:
        """Annuler un projet"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        project.cancel()
        
        # Statistiques
        self.stats["projects_cancelled"] += 1
        
        self.logger.info(f"Projet annulé: {project.project_id}")
        
        return True
    
    def get_project(self, project_id: str) -> Optional[ConstructionProject]:
        """Obtenir un projet"""
        return self.projects.get(project_id)
    
    def get_projects_by_owner(self, owner_id: str) -> List[ConstructionProject]:
        """Obtenir les projets d'un propriétaire"""
        return [p for p in self.projects.values() if p.owner_id == owner_id]
    
    def get_projects_by_group(self, group_id: str) -> List[ConstructionProject]:
        """Obtenir les projets d'un groupe"""
        return [p for p in self.projects.values() if p.group_id == group_id]
    
    def get_nearby_projects(self, position: Vector2, radius: float) -> List[ConstructionProject]:
        """Obtenir les projets à proximité"""
        return [
            p for p in self.projects.values()
            if p.position.distance_to(position) <= radius
        ]
    
    def get_blueprints(self) -> List[Blueprint]:
        """Obtenir tous les plans de construction"""
        return [Blueprint.get_blueprint(st) for st in StructureType]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du système"""
        return {
            **self.stats,
            "active_projects": len([p for p in self.projects.values() if not p.is_complete and not p.is_cancelled]),
            "completed_projects": len([p for p in self.projects.values() if p.is_complete]),
            "cancelled_projects": len([p for p in self.projects.values() if p.is_cancelled])
        }
    
    def clear(self):
        """Effacer tous les projets"""
        self.projects.clear()
        self.stats = {
            "projects_started": 0,
            "projects_completed": 0,
            "projects_cancelled": 0,
            "total_structures": 0
        }
