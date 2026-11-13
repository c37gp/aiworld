"""
Classe ReproductionSystem - Système de reproduction pour AI World
"""

import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict

from ..config import config
from ..utils.vector import Vector2
from ..utils.logger import Logger
from ..agents.ai_agent import AIAgent
from ..world.world import World


class ReproductionMethod(Enum):
    """Méthodes de reproduction"""
    ASEXUAL = auto()      # Asexuée (clonage)
    SEXUAL = auto()        # Sexuée (deux parents)
    ARTIFICIAL = auto()    # Artificielle (création par un autre agent)


class ReproductionStatus(Enum):
    """Statuts de reproduction"""
    READY = auto()         # Prêt
    PREGNANT = auto()      # En gestation
    COOLDOWN = auto()      # En cooldown
    NOT_READY = auto()     # Pas prêt


@dataclass
class Offspring:
    """Représente un descendant"""
    offspring_id: str
    parent1_id: str
    parent2_id: Optional[str] = None
    
    # Héritage génétique
    genetic_code: Dict[str, Any] = field(default_factory=dict)
    
    # Traits hérités
    inherited_traits: Dict[str, float] = field(default_factory=dict)
    
    # Mutations
    mutations: List[str] = field(default_factory=list)
    
    def add_trait(self, trait_name: str, value: float, from_parent: str = None):
        """Ajouter un trait"""
        self.inherited_traits[trait_name] = value
        if from_parent:
            self.genetic_code[f"{trait_name}_source"] = from_parent


class ReproductionSystem:
    """
    Système de reproduction pour AI World.
    Gère la création de nouveaux agents par reproduction.
    """
    
    def __init__(self, world: World):
        """Initialiser le système de reproduction"""
        self.world = world
        self.logger = Logger("ReproductionSystem")
        
        # Agents en gestation
        self.pregnant_agents: Dict[str, float] = {}  # agent_id -> progression (0-1)
        
        # Cooldowns de reproduction
        self.cooldowns: Dict[str, float] = {}  # agent_id -> temps restant
        
        # Statistiques
        self.stats = {
            "total_births": 0,
            "asexual_reproductions": 0,
            "sexual_reproductions": 0,
            "artificial_reproductions": 0,
            "mutations": 0
        }
        
        # Paramètres
        self.gestation_time = 5.0  # Temps de gestation (secondes)
        self.cooldown_time = config.agent.reproduction_cooldown
        self.min_reproduction_age = config.agent.reproduction_age
        
        # Génétique
        self.mutation_rate = 0.05  # Taux de mutation
        self.mutation_intensity = 0.1  # Intensité des mutations
    
    def update(self, delta_time: float):
        """Mettre à jour le système"""
        # Mettre à jour la gestation
        new_births = []
        
        for agent_id, progress in list(self.pregnant_agents.items()):
            new_progress = progress + delta_time / self.gestation_time
            
            if new_progress >= 1.0:
                new_births.append(agent_id)
                del self.pregnant_agents[agent_id]
            else:
                self.pregnant_agents[agent_id] = new_progress
        
        # Traiter les naissances
        for agent_id in new_births:
            self._give_birth(agent_id)
        
        # Mettre à jour les cooldowns
        for agent_id, remaining in list(self.cooldowns.items()):
            new_remaining = remaining - delta_time
            
            if new_remaining <= 0:
                del self.cooldowns[agent_id]
            else:
                self.cooldowns[agent_id] = new_remaining
    
    def can_reproduce(self, agent: AIAgent) -> ReproductionStatus:
        """Vérifier si un agent peut se reproduire"""
        if agent.age < self.min_reproduction_age:
            return ReproductionStatus.NOT_READY
        
        if agent.agent_id in self.pregnant_agents:
            return ReproductionStatus.PREGNANT
        
        if agent.agent_id in self.cooldowns:
            return ReproductionStatus.COOLDOWN
        
        if agent.reproduction_ready:
            return ReproductionStatus.READY
        
        return ReproductionStatus.NOT_READY
    
    def reproduce_asexual(self, parent: AIAgent) -> Optional[AIAgent]:
        """Reproduction asexuée (clonage)"""
        status = self.can_reproduce(parent)
        
        if status != ReproductionStatus.READY:
            return None
        
        # Vérifier si le parent a assez de ressources
        if sum(parent.inventory.values()) < 50:
            return None
        
        # Créer un nouvel agent
        child_position = self._find_birth_position(parent.position)
        
        if not child_position:
            return None
        
        # Créer l'enfant
        child = self._create_offspring(parent, None, ReproductionMethod.ASEXUAL)
        child.position = child_position
        
        # Consommer des ressources
        for resource_type in parent.inventory:
            transfer = parent.inventory[resource_type] * 0.2
            parent.inventory[resource_type] -= transfer
            child.inventory[resource_type] += transfer
        
        # Mettre à jour le parent
        parent.reproduction_ready = False
        self.cooldowns[parent.agent_id] = self.cooldown_time
        
        # Statistiques
        self.stats["total_births"] += 1
        self.stats["asexual_reproductions"] += 1
        
        self.logger.info(f"Reproduction asexuée: {parent.name} -> {child.name}")
        
        return child
    
    def reproduce_sexual(self, parent1: AIAgent, parent2: AIAgent) -> Optional[AIAgent]:
        """Reproduction sexuée (deux parents)"""
        status1 = self.can_reproduce(parent1)
        status2 = self.can_reproduce(parent2)
        
        if status1 != ReproductionStatus.READY or status2 != ReproductionStatus.READY:
            return None
        
        # Vérifier si les parents sont proches
        if parent1.position.distance_to(parent2.position) > 50:
            return None
        
        # Vérifier si les parents ont assez de ressources
        if sum(parent1.inventory.values()) < 50 or sum(parent2.inventory.values()) < 50:
            return None
        
        # Créer un nouvel agent
        child_position = self._find_birth_position(parent1.position)
        
        if not child_position:
            return None
        
        # Créer l'enfant
        child = self._create_offspring(parent1, parent2, ReproductionMethod.SEXUAL)
        child.position = child_position
        
        # Consommer des ressources
        for resource_type in parent1.inventory:
            transfer = parent1.inventory[resource_type] * 0.1
            parent1.inventory[resource_type] -= transfer
            child.inventory[resource_type] += transfer
        
        for resource_type in parent2.inventory:
            transfer = parent2.inventory[resource_type] * 0.1
            parent2.inventory[resource_type] -= transfer
            child.inventory[resource_type] += transfer
        
        # Mettre à jour les parents
        parent1.reproduction_ready = False
        parent2.reproduction_ready = False
        self.cooldowns[parent1.agent_id] = self.cooldown_time
        self.cooldowns[parent2.agent_id] = self.cooldown_time
        
        # Statistiques
        self.stats["total_births"] += 1
        self.stats["sexual_reproductions"] += 1
        
        self.logger.info(f"Reproduction sexuée: {parent1.name} + {parent2.name} -> {child.name}")
        
        return child
    
    def create_artificial(self, creator: AIAgent, target_type: type = None) -> Optional[AIAgent]:
        """Création artificielle d'un agent"""
        # Vérifier si le créateur a assez de ressources
        if sum(creator.inventory.values()) < 100:
            return None
        
        # Créer un nouvel agent
        child_position = self._find_birth_position(creator.position)
        
        if not child_position:
            return None
        
        # Créer l'enfant
        child = self._create_offspring(creator, None, ReproductionMethod.ARTIFICIAL)
        child.position = child_position
        child.ai_type = creator.ai_type  # Même type d'IA
        
        # Consommer des ressources
        for resource_type in creator.inventory:
            transfer = creator.inventory[resource_type] * 0.5
            creator.inventory[resource_type] -= transfer
            child.inventory[resource_type] += transfer
        
        # Transmettre des connaissances
        for knowledge in creator.memory.get_all_knowledge():
            creator.memory.share_knowledge(knowledge.topic, child.memory)
        
        # Statistiques
        self.stats["total_births"] += 1
        self.stats["artificial_reproductions"] += 1
        creator.stats.agents_created += 1
        
        self.logger.info(f"Création artificielle: {creator.name} -> {child.name}")
        
        return child
    
    def _create_offspring(self, parent1: AIAgent, parent2: Optional[AIAgent], 
                          method: ReproductionMethod) -> AIAgent:
        """Créer un descendant"""
        # Générer un ID unique
        offspring_id = f"offspring_{self.stats['total_births']}"
        
        # Créer le nouvel agent
        child = AIAgent(
            world=self.world,
            position=parent1.position.copy(),
            ai_type=parent1.ai_type,
            name=f"Child_{parent1.name}"
        )
        child.agent_id = offspring_id
        
        # Héritage génétique
        if method == ReproductionMethod.ASEXUAL:
            # Cloner la personnalité avec de légères variations
            self._inherit_personality(child, parent1, None)
        
        elif method == ReproductionMethod.SEXUAL:
            # Mélanger les personnalités des deux parents
            self._inherit_personality(child, parent1, parent2)
        
        elif method == ReproductionMethod.ARTIFICIAL:
            # Copier la personnalité du créateur
            self._inherit_personality(child, parent1, None)
        
        # Appliquer des mutations
        self._apply_mutations(child)
        
        return child
    
    def _inherit_personality(self, child: AIAgent, parent1: AIAgent, parent2: Optional[AIAgent]):
        """Hériter de la personnalité"""
        if parent2:
            # Mélanger les traits des deux parents
            for trait in PersonalityTrait:
                value1 = parent1.personality.get_trait(trait)
                value2 = parent2.personality.get_trait(trait)
                
                # Moyenne avec une légère variation
                inherited_value = (value1 + value2) / 2
                inherited_value += random.uniform(-0.1, 0.1)
                inherited_value = max(0, min(1, inherited_value))
                
                child.personality.profile.set_trait(trait, inherited_value)
        else:
            # Cloner avec de légères variations
            for trait in PersonalityTrait:
                value = parent1.personality.get_trait(trait)
                inherited_value = value + random.uniform(-0.1, 0.1)
                inherited_value = max(0, min(1, inherited_value))
                
                child.personality.profile.set_trait(trait, inherited_value)
    
    def _apply_mutations(self, agent: AIAgent):
        """Appliquer des mutations aléatoires"""
        for trait in PersonalityTrait:
            if random.random() < self.mutation_rate:
                # Appliquer une mutation
                mutation = random.uniform(-self.mutation_intensity, self.mutation_intensity)
                new_value = agent.personality.get_trait(trait) + mutation
                new_value = max(0, min(1, new_value))
                
                agent.personality.profile.set_trait(trait, new_value)
                agent.personality.profile.traits[trait] = new_value
                
                self.stats["mutations"] += 1
                
                self.logger.debug(f"Mutation: {trait.name} -> {new_value:.2f}")
    
    def _find_birth_position(self, parent_position: Vector2) -> Optional[Vector2]:
        """Trouver une position de naissance valide"""
        for _ in range(10):
            offset = Vector2(
                random.uniform(-30, 30),
                random.uniform(-30, 30)
            )
            
            position = parent_position + offset
            
            if self.world.is_position_valid(position):
                return position
        
        # Si on ne trouve pas, retourner une position proche du centre
        return self.world.get_random_spawn_position()
    
    def _give_birth(self, parent_id: str):
        """Donner naissance"""
        # Dans une version avancée, on créerait le nouvel agent ici
        # Pour l'instant, la naissance est gérée dans les méthodes de reproduction
        pass
    
    def start_pregnancy(self, parent: AIAgent):
        """Commencer une grossesse"""
        self.pregnant_agents[parent.agent_id] = 0.0
        parent.reproduction_ready = False
        
        self.logger.info(f"Grossesse commencée: {parent.name}")
    
    def get_pregnancy_progress(self, agent_id: str) -> float:
        """Obtenir la progression de la grossesse"""
        return self.pregnant_agents.get(agent_id, 0.0)
    
    def get_cooldown_remaining(self, agent_id: str) -> float:
        """Obtenir le temps restant de cooldown"""
        return self.cooldowns.get(agent_id, 0.0)
    
    def find_mate(self, agent: AIAgent, radius: float = 100) -> Optional[AIAgent]:
        """Trouver un partenaire pour la reproduction"""
        # Dans une implémentation complète, on chercherait les agents à proximité
        # qui sont prêts à se reproduire et compatibles
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du système"""
        return {
            **self.stats,
            "pregnant_agents": len(self.pregnant_agents),
            "agents_in_cooldown": len(self.cooldowns)
        }
    
    def clear(self):
        """Effacer tous les états"""
        self.pregnant_agents.clear()
        self.cooldowns.clear()
        self.stats = {
            "total_births": 0,
            "asexual_reproductions": 0,
            "sexual_reproductions": 0,
            "artificial_reproductions": 0,
            "mutations": 0
        }
