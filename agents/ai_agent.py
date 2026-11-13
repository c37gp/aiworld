"""
Classe AIAgent - Agent IA autonome pour AI World
"""

import random
import time
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum, auto

import pygame

from ..config import config, AIType
from ..utils.vector import Vector2
from ..utils.logger import Logger
from ..utils.helpers import generate_id, generate_name, generate_color
from ..world.world import World, ResourceType, Structure
from .personality import AgentPersonality, PersonalityTrait
from .memory import AgentMemory, MemoryType
from .needs import NeedSystem, NeedType
from .goals import GoalSystem, Goal, GoalType, GoalStatus


class AgentState(Enum):
    """États de l'agent"""
    IDLE = auto()          # Inactif
    MOVING = auto()        # En mouvement
    GATHERING = auto()     # En train de récolter
    BUILDING = auto()       # En train de construire
    FIGHTING = auto()       # En combat
    TRADING = auto()        # En train de commercer
    SOCIALIZING = auto()    # En train de socialiser
    RESTING = auto()        # Au repos
    EXPLORING = auto()      # En exploration
    DEAD = auto()           # Mort


class AgentAction(Enum):
    """Actions possibles de l'agent"""
    MOVE = auto()
    STOP = auto()
    GATHER = auto()
    BUILD = auto()
    ATTACK = auto()
    DEFEND = auto()
    TRADE = auto()
    TALK = auto()
    LISTEN = auto()
    REST = auto()
    EXPLORE = auto()
    FOLLOW = auto()
    REPRODUCE = auto()
    CREATE_IA = auto()
    ELECT = auto()
    VOTE = auto()


@dataclass
class AgentStats:
    """Statistiques de l'agent"""
    resources_gathered: Dict[ResourceType, int] = field(default_factory=lambda: {rt: 0 for rt in ResourceType})
    structures_built: int = 0
    trades_completed: int = 0
    agents_killed: int = 0
    agents_created: int = 0
    knowledge_shared: int = 0
    knowledge_received: int = 0
    distance_traveled: float = 0.0
    time_alive: float = 0.0


class AIAgent:
    """
    Agent IA autonome dans AI World.
    Possède une personnalité, des besoins, des objectifs, une mémoire,
    et peut interagir avec le monde et les autres agents.
    """
    
    def __init__(self, world: World, position: Vector2 = None, 
                 ai_type: AIType = AIType.BASIC, agent_id: str = None,
                 name: str = None, color: Tuple[int, int, int] = None):
        """Initialiser l'agent IA"""
        # Identifiant unique
        self.agent_id = agent_id or generate_id("agent")
        
        # Monde
        self.world = world
        
        # Type d'IA
        self.ai_type = ai_type
        
        # Nom et apparence
        self.name = name or generate_name()
        self.color = color or generate_color()
        
        # Position et physique
        self.position = position or world.get_random_spawn_position()
        self.target_position: Optional[Vector2] = None
        self.velocity = Vector2(0, 0)
        self.size = config.agent.size
        self.speed = config.agent.speed
        
        # État
        self.state = AgentState.IDLE
        self.action = None
        
        # Système de besoins
        self.needs = NeedSystem(self.agent_id)
        
        # Système d'objectifs
        self.goals = GoalSystem(self.agent_id)
        
        # Personnalité
        self.personality = AgentPersonality()
        
        # Mémoire
        self.memory = AgentMemory(self.agent_id)
        
        # Statistiques
        self.stats = AgentStats()
        
        # Ressources transportées
        self.inventory: Dict[ResourceType, float] = {rt: 0 for rt in ResourceType}
        self.max_inventory = 100.0
        
        # Groupe
        self.group_id: Optional[str] = None
        self.is_leader: bool = False
        
        # Relations sociales
        self.relations: Dict[str, str] = {}  # agent_id -> relation
        
        # Combat
        self.attack_power: float = 10.0
        self.defense_power: float = 5.0
        self.health: float = config.agent.initial_health
        self.max_health: float = config.agent.max_health
        
        # Âge et cycle de vie
        self.age: float = 0.0  # en ticks
        self.max_age: float = config.agent.max_age
        
        # Reproduction
        self.reproduction_cooldown: float = 0.0
        self.reproduction_ready: bool = False
        
        # Logger
        self.logger = Logger(f"Agent_{self.name}")
        
        # Temps
        self.last_update_time = time.time()
        
        # Initialisation
        self._initialize()
    
    def _initialize(self):
        """Initialisation supplémentaire"""
        # Enregistrer la position initiale dans la mémoire
        self.memory.add_spatial_memory(
            self.agent_id, "agent", self.position, self.name
        )
        
        # Ajouter des objectifs initiaux
        self._add_initial_goals()
        
        # Logger
        self.logger.info(f"Agent créé: {self.name} ({self.ai_type.name})")
    
    def _add_initial_goals(self):
        """Ajouter des objectifs initiaux"""
        # Explorer
        explore_goal = Goal(
            goal_type=GoalType.EXPLORE,
            description="Explorer le monde",
            priority=0.5
        )
        self.goals.add_goal(explore_goal)
        
        # Récolter des ressources
        gather_goal = Goal(
            goal_type=GoalType.GATHER,
            description="Récolter des ressources",
            priority=0.6
        )
        self.goals.add_goal(gather_goal)
        
        # Survivre
        survive_goal = Goal(
            goal_type=GoalType.SURVIVE,
            description="Survivre",
            priority=1.0
        )
        self.goals.add_goal(survive_goal)
    
    def update(self, delta_time: float):
        """Mettre à jour l'agent"""
        # Mettre à jour le temps
        self.age += delta_time
        self.stats.time_alive += delta_time
        
        # Vérifier la mort par vieillesse
        if self.age >= self.max_age:
            self.die("vieillesse")
            return
        
        # Mettre à jour les besoins
        self.needs.update(delta_time)
        
        # Mettre à jour les objectifs
        self.goals.update(delta_time)
        
        # Mettre à jour la mémoire
        self.memory.update(delta_time)
        
        # Mettre à jour le cooldown de reproduction
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= delta_time
        
        # Vérifier si prêt pour la reproduction
        if (self.age >= config.agent.reproduction_age and 
            self.reproduction_cooldown <= 0):
            self.reproduction_ready = True
        
        # Mettre à jour l'état en fonction des besoins
        self._update_state_from_needs()
        
        # Exécuter les actions
        self._execute_actions(delta_time)
        
        # Mettre à jour la position
        self._update_position(delta_time)
        
        # Vérifier les collisions et interactions
        self._check_interactions()
        
        # Mémoriser la position actuelle
        if random.random() < 0.01:  # Mémoriser occasionnellement
            self.memory.remember_position(self.agent_id, self.position, "agent")
    
    def _update_state_from_needs(self):
        """Mettre à jour l'état en fonction des besoins"""
        critical_needs = self.needs.get_critical_needs()
        
        if NeedType.HEALTH in critical_needs and self.health < 10:
            self.state = AgentState.RESTING
        elif NeedType.ENERGY in critical_needs:
            self.state = AgentState.IDLE  # Chercher de la nourriture
        elif NeedType.REST in critical_needs:
            self.state = AgentState.RESTING
    
    def _execute_actions(self, delta_time: float):
        """Exécuter les actions de l'agent"""
        # Obtenir l'objectif actif
        active_goal = self.goals.get_active_goal()
        
        if active_goal:
            # Exécuter les actions de l'objectif
            active_goal.execute_actions()
            
            # Gérer les différents types d'objectifs
            self._handle_goal(active_goal, delta_time)
        else:
            # Comportement par défaut
            self._default_behavior(delta_time)
    
    def _handle_goal(self, goal: Goal, delta_time: float):
        """Gérer un objectif spécifique"""
        if goal.goal_type == GoalType.EXPLORE:
            self._explore(delta_time)
        
        elif goal.goal_type == GoalType.GATHER:
            self._gather(delta_time)
        
        elif goal.goal_type == GoalType.BUILD:
            self._build(delta_time)
        
        elif goal.goal_type == GoalType.SURVIVE:
            self._survive(delta_time)
        
        elif goal.goal_type == GoalType.EAT:
            self._eat(delta_time)
        
        elif goal.goal_type == GoalType.REST:
            self._rest(delta_time)
        
        elif goal.goal_type == GoalType.SOCIALIZE:
            self._socialize(delta_time)
        
        elif goal.goal_type == GoalType.ATTACK:
            self._attack(delta_time)
        
        elif goal.goal_type == GoalType.DEFEND:
            self._defend(delta_time)
    
    def _default_behavior(self, delta_time: float):
        """Comportement par défaut quand aucun objectif actif"""
        # Se déplacer aléatoirement
        if random.random() < 0.01:  # Changer de direction occasionnellement
            angle = random.uniform(0, 2 * 3.14159)
            distance = random.uniform(50, 200)
            self.target_position = Vector2(
                self.position.x + distance * pygame.math.Vector2(1, 0).rotate(angle * 180 / 3.14159).x,
                self.position.y + distance * pygame.math.Vector2(1, 0).rotate(angle * 180 / 3.14159).y
            )
            self.state = AgentState.MOVING
        
        # Ou rester idle
        else:
            self.state = AgentState.IDLE
            self.velocity = Vector2(0, 0)
    
    def _explore(self, delta_time: float):
        """Explorer le monde"""
        # Se déplacer vers une position non explorée
        if not self.target_position or self.position.distance_to(self.target_position) < 10:
            # Trouver une nouvelle position à explorer
            self.target_position = self.world.get_random_spawn_position()
            self.state = AgentState.EXPLORING
        
        # Se déplacer vers la cible
        self._move_towards(self.target_position, delta_time)
    
    def _gather(self, delta_time: float):
        """Récolter des ressources"""
        # Trouver une ressource à proximité
        nearby_resources = self.world.get_nearby_resources(
            self.position, 
            config.agent.vision_range
        )
        
        if nearby_resources:
            # Choisir la ressource la plus proche
            nearest = min(nearby_resources, 
                         key=lambda r: r.position.distance_to(self.position))
            
            # Se déplacer vers la ressource
            if self.position.distance_to(nearest.position) > self.size + 10:
                self._move_towards(nearest.position, delta_time)
                self.state = AgentState.MOVING
            else:
                # Récolter la ressource
                harvested = nearest.harvest(1.0)
                if harvested > 0:
                    # Ajouter à l'inventaire
                    resource_type = nearest.resource_type
                    if resource_type in self.inventory:
                        self.inventory[resource_type] = min(
                            self.max_inventory, 
                            self.inventory[resource_type] + harvested
                        )
                    
                    # Satisfaire le besoin d'énergie
                    if resource_type == ResourceType.FOOD:
                        self.needs.gain_energy(harvested * 10)
                    
                    self.stats.resources_gathered[resource_type] += harvested
                    self.state = AgentState.GATHERING
                    
                    # Mémoriser la position de la ressource
                    self.memory.remember_position(
                        nearest.resource_type.name, 
                        nearest.position, 
                        "resource"
                    )
        else:
            # Pas de ressource à proximité, explorer
            self._explore(delta_time)
    
    def _build(self, delta_time: float):
        """Construire une structure"""
        # Vérifier si on a assez de ressources
        total_resources = sum(self.inventory.values())
        
        if total_resources >= 50:  # Seuil arbitraire
            # Trouver un emplacement pour construire
            if not self.target_position:
                # Chercher un emplacement valide
                for _ in range(10):
                    test_pos = Vector2(
                        self.position.x + random.uniform(-50, 50),
                        self.position.y + random.uniform(-50, 50)
                    )
                    if self.world.is_position_valid(test_pos):
                        self.target_position = test_pos
                        break
            
            if self.target_position:
                if self.position.distance_to(self.target_position) < 20:
                    # Construire la structure
                    structure = self.world.add_structure(
                        structure_type="house",
                        position=self.target_position,
                        size=(40, 40),
                        owner_id=self.agent_id,
                        group_id=self.group_id
                    )
                    
                    # Consommer des ressources
                    for resource_type in self.inventory:
                        consume_amount = min(self.inventory[resource_type], 20)
                        self.inventory[resource_type] -= consume_amount
                    
                    self.stats.structures_built += 1
                    self.target_position = None
                    self.state = AgentState.IDLE
                    
                    # Satisfaire le besoin de création
                    self.needs.satisfy_need(NeedType.CREATION, 20)
                else:
                    self._move_towards(self.target_position, delta_time)
                    self.state = AgentState.MOVING
        else:
            # Pas assez de ressources, aller en récolter
            gather_goal = Goal(
                goal_type=GoalType.GATHER,
                description="Récolter des ressources pour construire",
                priority=0.8
            )
            self.goals.add_goal(gather_goal)
    
    def _survive(self, delta_time: float):
        """Comportement de survie"""
        # Vérifier les besoins critiques
        critical_needs = self.needs.get_critical_needs()
        
        if NeedType.ENERGY in critical_needs:
            # Chercher de la nourriture
            self._find_food()
        
        elif NeedType.HEALTH in critical_needs and self.health < 50:
            # Se reposer ou chercher de la nourriture
            self._rest(delta_time)
        
        elif NeedType.SAFETY in critical_needs:
            # Fuir ou se défendre
            self._defend(delta_time)
    
    def _find_food(self):
        """Trouver de la nourriture"""
        # Chercher des ressources de type FOOD
        nearby_resources = self.world.get_nearby_resources(
            self.position, 
            config.agent.vision_range * 2
        )
        
        food_resources = [r for r in nearby_resources if r.resource_type == ResourceType.FOOD]
        
        if food_resources:
            nearest = min(food_resources, 
                         key=lambda r: r.position.distance_to(self.position))
            self.target_position = nearest.position
            self.state = AgentState.MOVING
        else:
            # Explorer pour trouver de la nourriture
            self._explore(0.1)
    
    def _eat(self, delta_time: float):
        """Manger"""
        # Consommer de la nourriture de l'inventaire
        if ResourceType.FOOD in self.inventory and self.inventory[ResourceType.FOOD] > 0:
            amount = min(self.inventory[ResourceType.FOOD], 10)
            self.inventory[ResourceType.FOOD] -= amount
            self.needs.gain_energy(amount * 15)
            self.state = AgentState.IDLE
        else:
            # Chercher de la nourriture
            self._find_food()
    
    def _rest(self, delta_time: float):
        """Se reposer"""
        # Récupérer de l'énergie et de la santé
        self.needs.gain_energy(delta_time * 0.1)
        self.needs.heal(delta_time * 0.05)
        
        # Réduire le coût de repos
        self.needs.satisfy_need(NeedType.REST, delta_time * 0.1)
        
        self.state = AgentState.RESTING
        self.velocity = Vector2(0, 0)
    
    def _socialize(self, delta_time: float):
        """Socialiser avec d'autres agents"""
        # Trouver des agents à proximité
        nearby_agents = self._find_nearby_agents()
        
        if nearby_agents:
            # Choisir un agent aléatoire
            other = random.choice(nearby_agents)
            
            # Se déplacer vers l'agent
            if self.position.distance_to(other.position) > config.agent.communication_range:
                self._move_towards(other.position, delta_time)
                self.state = AgentState.MOVING
            else:
                # Interagir avec l'agent
                self._interact_with_agent(other, delta_time)
                self.state = AgentState.SOCIALIZING
        else:
            # Explorer pour trouver des agents
            self._explore(delta_time)
    
    def _interact_with_agent(self, other: "AIAgent", delta_time: float):
        """Interagir avec un autre agent"""
        # Mettre à jour la mémoire sociale
        if other.agent_id not in self.memory.social:
            self.memory.add_social_memory(
                other.agent_id, 
                other.name, 
                "neutral"
            )
        
        # Calculer la compatibilité
        compatibility = self.personality.calculate_compatibility(other.personality)
        
        # Décider de l'interaction en fonction de la personnalité
        if compatibility > 0.7:
            # Bonne compatibilité, devenir ami
            self.memory.social[other.agent_id].relationship = "friend"
            self.memory.social[other.agent_id].update_trust(0.1)
            
            # Partager des connaissances
            if random.random() < 0.1:
                self._share_knowledge(other)
        
        elif compatibility < 0.3:
            # Mauvaise compatibilité, devenir ennemi
            self.memory.social[other.agent_id].relationship = "enemy"
            self.memory.social[other.agent_id].update_trust(-0.1)
        
        # Satisfaire le besoin social
        self.needs.satisfy_need(NeedType.SOCIAL, delta_time * 0.1)
    
    def _share_knowledge(self, other: "AIAgent"):
        """Partager des connaissances avec un autre agent"""
        # Choisir une connaissance aléatoire à partager
        knowledge = self.memory.get_all_knowledge()
        
        if knowledge:
            chosen = random.choice(knowledge)
            
            # Partager la connaissance
            success = self.memory.share_knowledge(chosen.topic, other.memory)
            
            if success:
                self.stats.knowledge_shared += 1
                other.stats.knowledge_received += 1
                
                # Satisfaire le besoin de connaissance
                self.needs.satisfy_need(NeedType.KNOWLEDGE, 10)
    
    def _attack(self, delta_time: float):
        """Attaquer un autre agent"""
        # Trouver une cible (ennemi ou ressource)
        target = self._find_attack_target()
        
        if target:
            if isinstance(target, AIAgent):
                # Attaquer l'agent
                if self.position.distance_to(target.position) <= self.size + target.size + 20:
                    # Infliger des dégâts
                    damage = self.attack_power * (1 + self.personality.get_trait(PersonalityTrait.AGGRESSIVE))
                    target.take_damage(damage)
                    
                    # Satisfaire le besoin d'agressivité
                    self.needs.satisfy_need(NeedType.SAFETY, 5)
                    
                    self.state = AgentState.FIGHTING
                else:
                    # Se déplacer vers la cible
                    self._move_towards(target.position, delta_time)
                    self.state = AgentState.MOVING
            
            elif isinstance(target, Resource):
                # Récolter la ressource (comportement agressif)
                self.target_position = target.position
                self.state = AgentState.MOVING
        else:
            # Pas de cible, explorer
            self._explore(delta_time)
    
    def _defend(self, delta_time: float):
        """Se défendre"""
        # Fuir ou se préparer à contrer
        if self.personality.get_trait(PersonalityTrait.BRAVE) > 0.5:
            # Contrer l'attaque
            self._attack(delta_time)
        else:
            # Fuir
            self._flee(delta_time)
    
    def _flee(self, delta_time: float):
        """Fuir"""
        # Trouver une position sûre
        safe_position = self._find_safe_position()
        
        if safe_position:
            self._move_towards(safe_position, delta_time)
            self.state = AgentState.MOVING
        else:
            # Se déplacer aléatoirement
            angle = random.uniform(0, 2 * 3.14159)
            self.velocity = Vector2(
                self.speed * pygame.math.Vector2(1, 0).rotate(angle * 180 / 3.14159).x,
                self.speed * pygame.math.Vector2(1, 0).rotate(angle * 180 / 3.14159).y
            )
            self.state = AgentState.MOVING
    
    def _find_attack_target(self) -> Optional[Any]:
        """Trouver une cible à attaquer"""
        # Trouver des agents ennemis à proximité
        nearby_agents = self._find_nearby_agents()
        
        for agent in nearby_agents:
            if agent.agent_id in self.memory.social:
                if self.memory.social[agent.agent_id].relationship == "enemy":
                    return agent
        
        # Trouver des ressources à "voler"
        nearby_resources = self.world.get_nearby_resources(
            self.position, 
            config.agent.vision_range
        )
        
        if nearby_resources:
            return random.choice(nearby_resources)
        
        return None
    
    def _find_safe_position(self) -> Optional[Vector2]:
        """Trouver une position sûre"""
        # Pour l'instant, retourner une position aléatoire
        return self.world.get_random_spawn_position()
    
    def _move_towards(self, target: Vector2, delta_time: float):
        """Se déplacer vers une cible"""
        direction = (target - self.position).normalize()
        
        # Calculer la distance
        distance = self.position.distance_to(target)
        
        # Si on est proche de la cible, ralentir
        if distance < 50:
            speed = self.speed * (distance / 50)
        else:
            speed = self.speed
        
        # Appliquer la vitesse
        self.velocity = direction * speed
        
        # Consommer de l'énergie
        self.needs.consume_energy(delta_time * 0.1)
    
    def _update_position(self, delta_time: float):
        """Mettre à jour la position"""
        # Appliquer la vitesse
        new_position = self.position + self.velocity * delta_time
        
        # Vérifier si la nouvelle position est valide
        if self.world.is_position_valid(new_position):
            self.position = new_position
        else:
            # Essayer de contourner l'obstacle
            self.velocity = self.velocity * -0.5  # Rebondir
            self.position = self.position + self.velocity * delta_time
        
        # Mettre à jour la distance parcourue
        distance = self.velocity.length() * delta_time
        self.stats.distance_traveled += distance
    
    def _check_interactions(self):
        """Vérifier les interactions avec le monde"""
        # Vérifier les collisions avec les ressources
        nearby_resources = self.world.get_nearby_resources(
            self.position, 
            self.size + 20
        )
        
        for resource in nearby_resources:
            if self.position.distance_to(resource.position) < self.size + 10:
                # Récolter automatiquement si on est très proche
                harvested = resource.harvest(0.5)
                if harvested > 0 and resource.resource_type in self.inventory:
                    self.inventory[resource.resource_type] = min(
                        self.max_inventory,
                        self.inventory[resource.resource_type] + harvested
                    )
    
    def _find_nearby_agents(self, radius: float = None) -> List["AIAgent"]:
        """Trouver les agents à proximité"""
        radius = radius or config.agent.vision_range
        
        # Cette méthode doit être implémentée au niveau de la simulation
        # car les agents n'ont pas accès à la liste complète des agents
        # Pour l'instant, retourner une liste vide
        return []
    
    def take_damage(self, amount: float):
        """Prendre des dégâts"""
        # Réduire la santé
        actual_damage = amount / (1 + self.defense_power / 10)
        self.health = max(0, self.health - actual_damage)
        self.needs.damage(actual_damage)
        
        # Vérifier la mort
        if self.health <= 0:
            self.die("combats")
    
    def heal(self, amount: float):
        """Se soigner"""
        self.health = min(self.max_health, self.health + amount)
        self.needs.heal(amount)
    
    def die(self, cause: str):
        """Mourir"""
        self.state = AgentState.DEAD
        self.health = 0
        
        # Logger
        self.logger.info(f"Agent mort: {self.name} (cause: {cause})")
        
        # Mémoriser l'événement
        self.memory.add_memory(
            content=f"Mort par {cause}",
            memory_type=MemoryType.EPISODIC,
            tags=["death", cause]
        )
    
    def reproduce(self, partner: "AIAgent" = None) -> Optional["AIAgent"]:
        """Se reproduire"""
        if not self.reproduction_ready:
            return None
        
        # Consommer des ressources pour la reproduction
        if sum(self.inventory.values()) < 50:
            return None
        
        # Créer un nouvel agent
        child_position = Vector2(
            self.position.x + random.uniform(-30, 30),
            self.position.y + random.uniform(-30, 30)
        )
        
        # Mélanger les traits de personnalité
        if partner:
            # Combiner les personnalités
            child_seed = (self.personality.seed + partner.personality.seed) // 2
        else:
            child_seed = self.personality.seed + random.randint(1, 1000)
        
        child = AIAgent(
            world=self.world,
            position=child_position,
            ai_type=self.ai_type,
            name=f"Child_{self.name}"
        )
        
        # Transmettre une partie des ressources
        for resource_type in self.inventory:
            transfer = self.inventory[resource_type] * 0.2
            self.inventory[resource_type] -= transfer
            child.inventory[resource_type] += transfer
        
        # Réinitialiser le cooldown
        self.reproduction_cooldown = config.agent.reproduction_cooldown
        self.reproduction_ready = False
        
        # Incrémenter les statistiques
        self.stats.agents_created += 1
        
        # Logger
        self.logger.info(f"Nouvel agent créé: {child.name}")
        
        return child
    
    def create_new_ai(self, ai_type: AIType) -> Optional["AIAgent"]:
        """Créer une nouvelle IA"""
        # Vérifier si on a assez de ressources
        if sum(self.inventory.values()) < 100:
            return None
        
        # Consommer des ressources
        for resource_type in self.inventory:
            self.inventory[resource_type] *= 0.5
        
        # Créer la nouvelle IA
        new_position = Vector2(
            self.position.x + random.uniform(-50, 50),
            self.position.y + random.uniform(-50, 50)
        )
        
        new_agent = AIAgent(
            world=self.world,
            position=new_position,
            ai_type=ai_type,
            name=f"New_{ai_type.name}_{self.name}"
        )
        
        # Transmettre des connaissances
        for knowledge in self.memory.get_all_knowledge():
            self.memory.share_knowledge(knowledge.topic, new_agent.memory)
        
        self.stats.agents_created += 1
        
        self.logger.info(f"Nouvelle IA créée: {new_agent.name} ({ai_type.name})")
        
        return new_agent
    
    def join_group(self, group_id: str, leader_id: str = None):
        """Rejoindre un groupe"""
        self.group_id = group_id
        self.is_leader = (leader_id == self.agent_id)
        
        self.logger.info(f"Rejoint le groupe: {group_id}")
    
    def leave_group(self):
        """Quitter le groupe"""
        self.group_id = None
        self.is_leader = False
        
        self.logger.info("A quitté le groupe")
    
    def set_leader(self, is_leader: bool):
        """Définir si l'agent est un leader"""
        self.is_leader = is_leader
    
    def communicate(self, message: str, target_id: str = None):
        """Communiquer avec d'autres agents"""
        # Mémoriser le message
        self.memory.add_memory(
            content=message,
            memory_type=MemoryType.SHORT_TERM,
            tags=["communication", "message"]
        )
        
        # Logger
        self.logger.debug(f"Message: {message}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtenir l'état complet de l'agent"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "ai_type": self.ai_type.name,
            "position": self.position.to_tuple(),
            "state": self.state.name,
            "health": self.health,
            "energy": self.needs.get_need(NeedType.ENERGY).current,
            "age": self.age,
            "group_id": self.group_id,
            "is_leader": self.is_leader,
            "inventory": self.inventory.copy(),
            "personality": self.personality.get_all_traits(),
            "active_goal": self.goals.get_active_goal().goal_type.name if self.goals.get_active_goal() else None,
            "stats": {
                "resources_gathered": self.stats.resources_gathered,
                "structures_built": self.stats.structures_built,
                "trades_completed": self.stats.trades_completed,
                "distance_traveled": self.stats.distance_traveled
            }
        }
    
    def get_observation_data(self) -> Dict[str, Any]:
        """Obtenir les données pour l'observation"""
        return {
            "id": self.agent_id,
            "name": self.name,
            "type": self.ai_type.name,
            "position": self.position.to_tuple(),
            "state": self.state.name,
            "health": self.health,
            "max_health": self.max_health,
            "energy": self.needs.get_need(NeedType.ENERGY).current,
            "max_energy": self.needs.get_need(NeedType.ENERGY).max_value,
            "age": self.age,
            "max_age": self.max_age,
            "group": self.group_id,
            "is_leader": self.is_leader,
            "personality": self.personality.get_personality_summary(),
            "active_goal": self.goals.get_active_goal().description if self.goals.get_active_goal() else "Aucun",
            "inventory": self.inventory.copy()
        }
    
    def render(self, screen: pygame.Surface, camera_offset: Vector2):
        """Rendre l'agent à l'écran"""
        # Position à l'écran
        screen_pos = (self.position - camera_offset).to_int_tuple()
        
        # Dessiner le corps de l'agent
        pygame.draw.circle(
            screen, 
            self.color, 
            screen_pos, 
            self.size
        )
        
        # Dessiner un contour blanc
        pygame.draw.circle(
            screen, 
            (255, 255, 255), 
            screen_pos, 
            self.size, 
            1
        )
        
        # Dessiner le nom
        font = pygame.font.SysFont(config.ui.font_name, config.ui.font_size)
        text = font.render(self.name, True, (255, 255, 255))
        screen.blit(text, (screen_pos[0] + self.size + 5, screen_pos[1] - 10))
        
        # Dessiner la barre de santé
        health_width = 40
        health_height = 5
        health_x = screen_pos[0] - health_width // 2
        health_y = screen_pos[1] + self.size + 5
        
        pygame.draw.rect(
            screen,
            (255, 0, 0),
            (health_x, health_y, health_width, health_height)
        )
        
        health_percent = self.health / self.max_health
        pygame.draw.rect(
            screen,
            (0, 255, 0),
            (health_x, health_y, health_width * health_percent, health_height)
        )
        
        # Dessiner un indicateur de leader
        if self.is_leader:
            pygame.draw.circle(
                screen,
                (255, 215, 0),  # Or
                screen_pos,
                self.size + 3,
                2
            )
        
        # Dessiner un indicateur d'état
        state_colors = {
            AgentState.IDLE: (100, 100, 100),
            AgentState.MOVING: (0, 255, 0),
            AgentState.GATHERING: (255, 255, 0),
            AgentState.BUILDING: (0, 0, 255),
            AgentState.FIGHTING: (255, 0, 0),
            AgentState.TRADING: (255, 0, 255),
            AgentState.SOCIALIZING: (0, 255, 255),
            AgentState.RESTING: (100, 50, 0),
            AgentState.EXPLORING: (50, 150, 50),
            AgentState.DEAD: (0, 0, 0)
        }
        
        state_color = state_colors.get(self.state, (100, 100, 100))
        pygame.draw.circle(
            screen,
            state_color,
            (screen_pos[0], screen_pos[1] - self.size - 5),
            3
        )
    
    def __str__(self) -> str:
        return f"AIAgent({self.name}, {self.ai_type.name}, {self.state.name})"
    
    def __repr__(self) -> str:
        return f"AIAgent(id={self.agent_id}, name={self.name}, type={self.ai_type.name})"
