"""
Classe NeedSystem - Système de besoins pour les agents IA
"""

import random
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum, auto

from ..config import config
from ..utils.logger import Logger


class NeedType(Enum):
    """Types de besoins"""
    ENERGY = auto()      # Énergie (nourriture)
    HEALTH = auto()      # Santé
    REST = auto()        # Repos
    SOCIAL = auto()      # Interaction sociale
    SAFETY = auto()      # Sécurité
    EXPLORATION = auto() # Exploration
    CREATION = auto()    # Création/Construction
    KNOWLEDGE = auto()   # Apprentissage
    REPRODUCTION = auto() # Reproduction


@dataclass
class Need:
    """Représente un besoin"""
    need_type: NeedType
    current: float = 100.0
    max_value: float = 100.0
    decay_rate: float = 0.01
    critical_threshold: float = 20.0
    satisfied_threshold: float = 80.0
    
    def __post_init__(self):
        self.current = min(self.current, self.max_value)
    
    def update(self, delta_time: float):
        """Mettre à jour le besoin (décroissance)"""
        self.current = max(0, self.current - self.decay_rate * delta_time)
    
    def satisfy(self, amount: float):
        """Satisfaire le besoin"""
        self.current = min(self.max_value, self.current + amount)
    
    def is_critical(self) -> bool:
        """Vérifier si le besoin est critique"""
        return self.current <= self.critical_threshold
    
    def is_satisfied(self) -> bool:
        """Vérifier si le besoin est satisfait"""
        return self.current >= self.satisfied_threshold
    
    def get_urgency(self) -> float:
        """Obtenir l'urgence du besoin (0-1)"""
        if self.current >= self.satisfied_threshold:
            return 0.0
        return 1.0 - (self.current / self.satisfied_threshold)


class NeedSystem:
    """
    Système de gestion des besoins pour un agent IA.
    Les besoins influencent les motivations et les actions de l'agent.
    """
    
    def __init__(self, agent_id: str):
        """Initialiser le système de besoins"""
        self.agent_id = agent_id
        self.logger = Logger(f"Needs_{agent_id}")
        
        # Initialiser les besoins
        self.needs: Dict[NeedType, Need] = {}
        self._initialize_needs()
        
        # Actions pour satisfaire les besoins
        self.satisfaction_actions: Dict[NeedType, List[Callable]] = {}
        
        # Historique des besoins
        self.history: Dict[NeedType, List[float]] = {}
        for need_type in NeedType:
            self.history[need_type] = []
    
    def _initialize_needs(self):
        """Initialiser les besoins avec des valeurs par défaut"""
        # Énergie
        self.needs[NeedType.ENERGY] = Need(
            need_type=NeedType.ENERGY,
            current=config.agent.initial_energy,
            max_value=config.agent.max_energy,
            decay_rate=config.agent.energy_decay_rate,
            critical_threshold=20.0,
            satisfied_threshold=80.0
        )
        
        # Santé
        self.needs[NeedType.HEALTH] = Need(
            need_type=NeedType.HEALTH,
            current=config.agent.initial_health,
            max_value=config.agent.max_health,
            decay_rate=0.001,  # Décroissance très lente
            critical_threshold=10.0,
            satisfied_threshold=90.0
        )
        
        # Repos
        self.needs[NeedType.REST] = Need(
            need_type=NeedType.REST,
            current=100.0,
            max_value=100.0,
            decay_rate=0.005,
            critical_threshold=30.0,
            satisfied_threshold=80.0
        )
        
        # Social
        self.needs[NeedType.SOCIAL] = Need(
            need_type=NeedType.SOCIAL,
            current=50.0,
            max_value=100.0,
            decay_rate=0.002,
            critical_threshold=10.0,
            satisfied_threshold=70.0
        )
        
        # Sécurité
        self.needs[NeedType.SAFETY] = Need(
            need_type=NeedType.SAFETY,
            current=100.0,
            max_value=100.0,
            decay_rate=0.0,
            critical_threshold=30.0,
            satisfied_threshold=80.0
        )
        
        # Exploration
        self.needs[NeedType.EXPLORATION] = Need(
            need_type=NeedType.EXPLORATION,
            current=0.0,
            max_value=100.0,
            decay_rate=0.001,
            critical_threshold=10.0,
            satisfied_threshold=70.0
        )
        
        # Création
        self.needs[NeedType.CREATION] = Need(
            need_type=NeedType.CREATION,
            current=0.0,
            max_value=100.0,
            decay_rate=0.001,
            critical_threshold=10.0,
            satisfied_threshold=60.0
        )
        
        # Connaissance
        self.needs[NeedType.KNOWLEDGE] = Need(
            need_type=NeedType.KNOWLEDGE,
            current=0.0,
            max_value=100.0,
            decay_rate=0.0005,
            critical_threshold=10.0,
            satisfied_threshold=70.0
        )
        
        # Reproduction
        self.needs[NeedType.REPRODUCTION] = Need(
            need_type=NeedType.REPRODUCTION,
            current=0.0,
            max_value=100.0,
            decay_rate=0.0,
            critical_threshold=50.0,
            satisfied_threshold=80.0
        )
    
    def update(self, delta_time: float):
        """Mettre à jour tous les besoins"""
        for need in self.needs.values():
            need.update(delta_time)
            
            # Enregistrer dans l'historique
            self.history[need.need_type].append(need.current)
            if len(self.history[need.need_type]) > 1000:
                self.history[need.need_type].pop(0)
    
    def get_need(self, need_type: NeedType) -> Need:
        """Obtenir un besoin spécifique"""
        return self.needs.get(need_type, Need(need_type))
    
    def satisfy_need(self, need_type: NeedType, amount: float):
        """Satisfaire un besoin"""
        if need_type in self.needs:
            self.needs[need_type].satisfy(amount)
            self.logger.debug(f"Besoin {need_type.name} satisfait de {amount}")
    
    def get_most_urgent_need(self) -> Tuple[NeedType, float]:
        """Obtenir le besoin le plus urgent"""
        max_urgency = -1
        most_urgent = None
        
        for need_type, need in self.needs.items():
            urgency = need.get_urgency()
            if urgency > max_urgency:
                max_urgency = urgency
                most_urgent = need_type
        
        return (most_urgent, max_urgency) if most_urgent else (None, 0)
    
    def get_need_urgencies(self) -> Dict[NeedType, float]:
        """Obtenir les urgences de tous les besoins"""
        return {need_type: need.get_urgency() for need_type, need in self.needs.items()}
    
    def get_critical_needs(self) -> List[NeedType]:
        """Obtenir les besoins critiques"""
        return [need_type for need_type, need in self.needs.items() if need.is_critical()]
    
    def get_satisfied_needs(self) -> List[NeedType]:
        """Obtenir les besoins satisfaits"""
        return [need_type for need_type, need in self.needs.items() if need.is_satisfied()]
    
    def register_satisfaction_action(self, need_type: NeedType, action: Callable):
        """Enregistrer une action pour satisfaire un besoin"""
        if need_type not in self.satisfaction_actions:
            self.satisfaction_actions[need_type] = []
        self.satisfaction_actions[need_type].append(action)
    
    def get_satisfaction_actions(self, need_type: NeedType) -> List[Callable]:
        """Obtenir les actions pour satisfaire un besoin"""
        return self.satisfaction_actions.get(need_type, [])
    
    def get_motivation_vector(self) -> Dict[NeedType, float]:
        """
        Obtenir un vecteur de motivation basé sur les besoins.
        Les besoins non satisfaits ont une motivation plus élevée.
        """
        motivations = {}
        for need_type, need in self.needs.items():
            # Motivation = 1 - satisfaction
            satisfaction = need.current / need.max_value
            motivations[need_type] = 1.0 - satisfaction
        
        return motivations
    
    def get_overall_motivation(self) -> float:
        """Obtenir la motivation globale (0-1)"""
        motivations = self.get_motivation_vector()
        total = sum(motivations.values())
        return total / len(motivations) if motivations else 0
    
    def damage(self, amount: float):
        """Infliger des dégâts (réduit la santé)"""
        if NeedType.HEALTH in self.needs:
            self.needs[NeedType.HEALTH].current = max(
                0, 
                self.needs[NeedType.HEALTH].current - amount
            )
            self.logger.debug(f"Dégâts: -{amount} santé")
    
    def heal(self, amount: float):
        """Soigner (augmente la santé)"""
        if NeedType.HEALTH in self.needs:
            self.needs[NeedType.HEALTH].satisfy(amount)
            self.logger.debug(f"Soins: +{amount} santé")
    
    def consume_energy(self, amount: float):
        """Consommer de l'énergie"""
        if NeedType.ENERGY in self.needs:
            self.needs[NeedType.ENERGY].current = max(
                0,
                self.needs[NeedType.ENERGY].current - amount
            )
    
    def gain_energy(self, amount: float):
        """Gagner de l'énergie"""
        if NeedType.ENERGY in self.needs:
            self.needs[NeedType.ENERGY].satisfy(amount)
    
    def get_stats(self) -> Dict:
        """Obtenir les statistiques des besoins"""
        return {
            need_type.name: {
                "current": need.current,
                "max": need.max_value,
                "urgency": need.get_urgency(),
                "is_critical": need.is_critical(),
                "is_satisfied": need.is_satisfied()
            }
            for need_type, need in self.needs.items()
        }
    
    def reset_need(self, need_type: NeedType):
        """Réinitialiser un besoin à sa valeur maximale"""
        if need_type in self.needs:
            self.needs[need_type].current = self.needs[need_type].max_value
