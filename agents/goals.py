"""
Classe GoalSystem - Système d'objectifs pour les agents IA
"""

import random
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque

from ..config import config
from ..utils.vector import Vector2
from ..utils.logger import Logger
from .needs import NeedType


class GoalType(Enum):
    """Types d'objectifs"""
    SURVIVE = auto()        # Survivre (besoins de base)
    EXPLORE = auto()        # Explorer le monde
    GATHER = auto()         # Récolter des ressources
    BUILD = auto()          # Construire une structure
    TRADE = auto()          # Commercer
    SOCIALIZE = auto()      # Socialiser
    FORM_GROUP = auto()     # Former un groupe
    LEAD_GROUP = auto()     # Diriger un groupe
    ATTACK = auto()         # Attaquer
    DEFEND = auto()         # Défendre
    REPRODUCE = auto()      # Se reproduire
    LEARN = auto()          # Apprendre
    TEACH = auto()          # Enseigner
    CREATE_RULE = auto()    # Créer une règle
    FOLLOW_RULE = auto()    # Suivre une règle
    REST = auto()           # Se reposer
    EAT = auto()            # Manger


class GoalStatus(Enum):
    """Statuts d'objectif"""
    PENDING = auto()    # En attente
    ACTIVE = auto()     # Actif
    COMPLETED = auto()  # Complété
    FAILED = auto()     # Échoué
    ABANDONED = auto()  # Abandonné


@dataclass
class Goal:
    """Représente un objectif"""
    goal_type: GoalType
    description: str
    priority: float = 0.5  # Priorité (0-1)
    status: GoalStatus = GoalStatus.PENDING
    target: Optional[Any] = None  # Cible (position, agent, ressource, etc.)
    progress: float = 0.0  # Progression (0-1)
    deadline: Optional[float] = None  # Échéance (temps de simulation)
    
    # Actions associées
    actions: List[Callable] = field(default_factory=list)
    
    # Conditions de succès/échec
    success_condition: Optional[Callable[[], bool]] = None
    failure_condition: Optional[Callable[[], bool]] = None
    
    def __post_init__(self):
        if not hasattr(self, 'actions'):
            self.actions = []
    
    def update(self, delta_time: float) -> GoalStatus:
        """Mettre à jour l'objectif, retourne le nouveau statut"""
        if self.status == GoalStatus.COMPLETED or self.status == GoalStatus.FAILED:
            return self.status
        
        # Vérifier les conditions
        if self.success_condition and self.success_condition():
            self.status = GoalStatus.COMPLETED
            return self.status
        
        if self.failure_condition and self.failure_condition():
            self.status = GoalStatus.FAILED
            return self.status
        
        # Vérifier l'échéance
        if self.deadline is not None and self.deadline <= 0:
            self.status = GoalStatus.FAILED
            return self.status
        
        if self.deadline is not None:
            self.deadline -= delta_time
        
        return self.status
    
    def activate(self):
        """Activer l'objectif"""
        self.status = GoalStatus.ACTIVE
    
    def complete(self):
        """Compléter l'objectif"""
        self.status = GoalStatus.COMPLETED
        self.progress = 1.0
    
    def fail(self):
        """Échouer l'objectif"""
        self.status = GoalStatus.FAILED
    
    def abandon(self):
        """Abandonner l'objectif"""
        self.status = GoalStatus.ABANDONED
    
    def add_action(self, action: Callable):
        """Ajouter une action à l'objectif"""
        self.actions.append(action)
    
    def execute_actions(self):
        """Exécuter toutes les actions"""
        for action in self.actions:
            action()


class GoalSystem:
    """
    Système de gestion des objectifs pour un agent IA.
    Permet de créer, prioriser et exécuter des objectifs.
    """
    
    def __init__(self, agent_id: str):
        """Initialiser le système d'objectifs"""
        self.agent_id = agent_id
        self.logger = Logger(f"Goals_{agent_id}")
        
        # Objectifs
        self.goals: List[Goal] = []
        self.active_goal: Optional[Goal] = None
        self.completed_goals: deque = deque(maxlen=100)
        self.failed_goals: deque = deque(maxlen=100)
        
        # Historique
        self.history: List[Goal] = []
        
        # Générateurs d'objectifs
        self.goal_generators: List[Callable[[], Optional[Goal]]] = []
        
        # Priorités des types d'objectifs
        self.type_priorities: Dict[GoalType, float] = {
            GoalType.SURVIVE: 1.0,
            GoalType.EAT: 0.9,
            GoalType.REST: 0.8,
            GoalType.DEFEND: 0.9,
            GoalType.ATTACK: 0.7,
            GoalType.GATHER: 0.6,
            GoalType.EXPLORE: 0.5,
            GoalType.BUILD: 0.6,
            GoalType.TRADE: 0.5,
            GoalType.SOCIALIZE: 0.4,
            GoalType.FORM_GROUP: 0.5,
            GoalType.LEAD_GROUP: 0.6,
            GoalType.REPRODUCE: 0.3,
            GoalType.LEARN: 0.4,
            GoalType.TEACH: 0.3,
            GoalType.CREATE_RULE: 0.2,
            GoalType.FOLLOW_RULE: 0.3
        }
    
    def add_goal(self, goal: Goal, auto_activate: bool = True) -> Goal:
        """Ajouter un objectif"""
        self.goals.append(goal)
        self.history.append(goal)
        
        self.logger.debug(f"Objectif ajouté: {goal.goal_type.name} - {goal.description}")
        
        if auto_activate and self.active_goal is None:
            self.activate_goal(goal)
        
        return goal
    
    def add_goal_from_needs(self, need_type: NeedType, need_value: float):
        """Créer un objectif à partir d'un besoin"""
        # Mapper les besoins aux objectifs
        need_to_goal = {
            NeedType.ENERGY: GoalType.EAT,
            NeedType.HEALTH: GoalType.SURVIVE,
            NeedType.REST: GoalType.REST,
            NeedType.SOCIAL: GoalType.SOCIALIZE,
            NeedType.SAFETY: GoalType.DEFEND,
            NeedType.EXPLORATION: GoalType.EXPLORE,
            NeedType.CREATION: GoalType.BUILD,
            NeedType.KNOWLEDGE: GoalType.LEARN,
            NeedType.REPRODUCTION: GoalType.REPRODUCE
        }
        
        goal_type = need_to_goal.get(need_type)
        if goal_type:
            # Calculer la priorité en fonction de l'urgence du besoin
            priority = min(1.0, need_value / 20.0)  # Échelle arbitraire
            
            goal = Goal(
                goal_type=goal_type,
                description=f"Satisfaire le besoin de {need_type.name.lower()}",
                priority=priority
            )
            
            self.add_goal(goal)
    
    def generate_goals_from_needs(self, needs: Dict[NeedType, float]):
        """Générer des objectifs à partir des besoins"""
        for need_type, urgency in needs.items():
            if urgency > 0.5:  # Seuil arbitraire
                self.add_goal_from_needs(need_type, urgency * 100)
    
    def activate_goal(self, goal: Goal):
        """Activer un objectif"""
        if self.active_goal:
            # Désactiver l'objectif actuel
            self.active_goal.status = GoalStatus.PENDING
        
        goal.activate()
        self.active_goal = goal
        
        self.logger.debug(f"Objectif activé: {goal.goal_type.name}")
    
    def update(self, delta_time: float):
        """Mettre à jour tous les objectifs"""
        # Mettre à jour l'objectif actif
        if self.active_goal:
            old_status = self.active_goal.status
            new_status = self.active_goal.update(delta_time)
            
            if new_status != old_status:
                if new_status == GoalStatus.COMPLETED:
                    self.completed_goals.append(self.active_goal)
                    self.logger.info(f"Objectif complété: {self.active_goal.goal_type.name}")
                    self.active_goal = None
                
                elif new_status == GoalStatus.FAILED:
                    self.failed_goals.append(self.active_goal)
                    self.logger.warning(f"Objectif échoué: {self.active_goal.goal_type.name}")
                    self.active_goal = None
        
        # Mettre à jour tous les objectifs
        for goal in self.goals[:]:
            if goal != self.active_goal:
                old_status = goal.status
                new_status = goal.update(delta_time)
                
                if new_status != old_status:
                    if new_status == GoalStatus.COMPLETED:
                        self.completed_goals.append(goal)
                        self.goals.remove(goal)
                    elif new_status == GoalStatus.FAILED:
                        self.failed_goals.append(goal)
                        self.goals.remove(goal)
        
        # Si aucun objectif actif, en sélectionner un
        if self.active_goal is None and self.goals:
            self._select_next_goal()
    
    def _select_next_goal(self):
        """Sélectionner le prochain objectif à activer"""
        # Calculer les priorités globales
        priorities = []
        for goal in self.goals:
            # Priorité = priorité de l'objectif * priorité du type
            type_priority = self.type_priorities.get(goal.goal_type, 0.5)
            global_priority = goal.priority * type_priority
            priorities.append((goal, global_priority))
        
        # Trier par priorité (descendant)
        priorities.sort(key=lambda x: x[1], reverse=True)
        
        # Sélectionner le meilleur
        if priorities:
            best_goal = priorities[0][0]
            self.activate_goal(best_goal)
    
    def get_active_goal(self) -> Optional[Goal]:
        """Obtenir l'objectif actif"""
        return self.active_goal
    
    def get_goals_by_type(self, goal_type: GoalType) -> List[Goal]:
        """Obtenir les objectifs d'un type spécifique"""
        return [g for g in self.goals if g.goal_type == goal_type]
    
    def get_goals_by_status(self, status: GoalStatus) -> List[Goal]:
        """Obtenir les objectifs avec un statut spécifique"""
        all_goals = self.goals + [self.active_goal] if self.active_goal else []
        return [g for g in all_goals if g.status == status]
    
    def remove_goal(self, goal: Goal) -> bool:
        """Supprimer un objectif"""
        if goal in self.goals:
            self.goals.remove(goal)
            return True
        return False
    
    def clear_goals(self):
        """Supprimer tous les objectifs"""
        self.goals.clear()
        self.active_goal = None
    
    def register_goal_generator(self, generator: Callable[[], Optional[Goal]]):
        """Enregistrer un générateur d'objectifs"""
        self.goal_generators.append(generator)
    
    def generate_goals(self):
        """Générer de nouveaux objectifs à partir des générateurs"""
        for generator in self.goal_generators:
            goal = generator()
            if goal:
                self.add_goal(goal)
    
    def get_next_action(self) -> Optional[Callable]:
        """Obtenir la prochaine action à exécuter"""
        if self.active_goal and self.active_goal.actions:
            return self.active_goal.actions[0]
        return None
    
    def get_stats(self) -> Dict:
        """Obtenir les statistiques des objectifs"""
        return {
            "total_goals": len(self.goals),
            "active_goal": self.active_goal.goal_type.name if self.active_goal else None,
            "completed_goals": len(self.completed_goals),
            "failed_goals": len(self.failed_goals),
            "goal_types": {
                gt.name: len(self.get_goals_by_type(gt))
                for gt in GoalType
            }
        }
    
    def get_priority_vector(self) -> Dict[GoalType, float]:
        """Obtenir un vecteur de priorités pour chaque type d'objectif"""
        return self.type_priorities.copy()
    
    def set_priority(self, goal_type: GoalType, priority: float):
        """Définir la priorité pour un type d'objectif"""
        self.type_priorities[goal_type] = max(0, min(1, priority))
