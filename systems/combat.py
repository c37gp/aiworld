"""
Classe CombatSystem - Système de combat pour AI World
"""

import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque

from ..config import config
from ..utils.vector import Vector2
from ..utils.logger import Logger
from ..agents.ai_agent import AIAgent, AgentState


class CombatType(Enum):
    """Types de combat"""
    MELEE = auto()         # Corps à corps
    RANGED = auto()        # À distance
    MAGIC = auto()         # Magique
    PSYCHIC = auto()       # Psychique


class CombatStatus(Enum):
    """Statuts de combat"""
    PENDING = auto()       # En attente
    ACTIVE = auto()        # Actif
    ENDED = auto()         # Terminé


class CombatResult(Enum):
    """Résultats de combat"""
    VICTORY = auto()       # Victoire
    DEFEAT = auto()        # Défaite
    DRAW = auto()          # Match nul
    RETREAT = auto()       # Retraite


@dataclass
class CombatAction:
    """Action de combat"""
    action_type: str  # "attack", "defend", "flee", "special"
    attacker_id: str
    target_id: str
    damage: float = 0.0
    accuracy: float = 1.0
    
    # Effets spéciaux
    effects: List[str] = field(default_factory=list)
    
    def apply(self, attacker: AIAgent, target: AIAgent) -> float:
        """Appliquer l'action"""
        if self.action_type == "attack":
            # Calculer les dégâts
            base_damage = attacker.attack_power
            
            # Prendre en compte l'exactitude
            if random.random() > self.accuracy:
                return 0.0
            
            # Prendre en compte la défense
            actual_damage = base_damage * (1 - target.defense_power / (target.defense_power + 20))
            
            # Appliquer les dégâts
            target.take_damage(actual_damage)
            
            return actual_damage
        
        return 0.0


@dataclass
class Combat:
    """Représente un combat entre agents"""
    combat_id: str
    attacker_id: str
    defender_id: str
    
    # Type de combat
    combat_type: CombatType = CombatType.MELEE
    
    # Statut
    status: CombatStatus = CombatStatus.PENDING
    
    # Historique des actions
    actions: List[CombatAction] = field(default_factory=list)
    
    # Statistiques
    rounds: int = 0
    total_damage: Dict[str, float] = field(default_factory=dict)  # agent_id -> dégâts infligés
    
    # Résultat
    result: Optional[CombatResult] = None
    winner_id: Optional[str] = None
    loser_id: Optional[str] = None
    
    def __post_init__(self):
        self.total_damage = {
            self.attacker_id: 0.0,
            self.defender_id: 0.0
        }
    
    def start(self):
        """Démarrer le combat"""
        self.status = CombatStatus.ACTIVE
        self.logger = Logger(f"Combat_{self.combat_id}")
        self.logger.info(f"Combat commencé: {self.attacker_id} vs {self.defender_id}")
    
    def end(self, result: CombatResult, winner_id: str = None, loser_id: str = None):
        """Terminer le combat"""
        self.status = CombatStatus.ENDED
        self.result = result
        self.winner_id = winner_id
        self.loser_id = loser_id
        
        self.logger.info(f"Combat terminé: {result.name}")
    
    def perform_round(self, attacker: AIAgent, defender: AIAgent) -> bool:
        """Effectuer un round de combat, retourne True si le combat continue"""
        if self.status != CombatStatus.ACTIVE:
            return False
        
        self.rounds += 1
        
        # Déterminer les actions
        attacker_action = self._get_attacker_action(attacker, defender)
        defender_action = self._get_defender_action(defender, attacker)
        
        # Appliquer les actions
        if attacker_action:
            damage = attacker_action.apply(attacker, defender)
            self.total_damage[attacker.agent_id] += damage
            self.actions.append(attacker_action)
        
        if defender_action:
            # Le défenseur peut contrer
            if defender_action.action_type == "attack":
                damage = defender_action.apply(defender, attacker)
                self.total_damage[defender.agent_id] += damage
                self.actions.append(defender_action)
        
        # Vérifier si le combat doit se terminer
        if attacker.state == AgentState.DEAD:
            self.end(CombatResult.DEFEAT, defender.agent_id, attacker.agent_id)
            return False
        
        if defender.state == AgentState.DEAD:
            self.end(CombatResult.VICTORY, attacker.agent_id, defender.agent_id)
            return False
        
        # Vérifier la retraite
        if self._check_retreat(attacker, defender):
            self.end(CombatResult.RETREAT, defender.agent_id, attacker.agent_id)
            return False
        
        if self._check_retreat(defender, attacker):
            self.end(CombatResult.RETREAT, attacker.agent_id, defender.agent_id)
            return False
        
        # Vérifier le nombre maximum de rounds
        if self.rounds >= 50:  # Limite arbitraire
            # Déterminer le gagnant en fonction des dégâts
            if self.total_damage[attacker.agent_id] > self.total_damage[defender.agent_id]:
                self.end(CombatResult.VICTORY, attacker.agent_id, defender.agent_id)
            elif self.total_damage[attacker.agent_id] < self.total_damage[defender.agent_id]:
                self.end(CombatResult.VICTORY, defender.agent_id, attacker.agent_id)
            else:
                self.end(CombatResult.DRAW)
            return False
        
        return True
    
    def _get_attacker_action(self, attacker: AIAgent, defender: AIAgent) -> CombatAction:
        """Obtenir l'action de l'attaquant"""
        # Basé sur la personnalité
        aggressiveness = attacker.personality.get_trait(PersonalityTrait.AGGRESSIVE)
        
        # Plus l'agent est agressif, plus il a de chances d'attaquer
        if random.random() < aggressiveness:
            return CombatAction(
                action_type="attack",
                attacker_id=attacker.agent_id,
                target_id=defender.agent_id,
                damage=attacker.attack_power,
                accuracy=0.8 + aggressiveness * 0.2
            )
        else:
            # Sinon, se défendre ou fuir
            if random.random() < 0.5:
                return CombatAction(
                    action_type="defend",
                    attacker_id=attacker.agent_id,
                    target_id=defender.agent_id
                )
            else:
                return CombatAction(
                    action_type="flee",
                    attacker_id=attacker.agent_id,
                    target_id=defender.agent_id
                )
    
    def _get_defender_action(self, defender: AIAgent, attacker: AIAgent) -> CombatAction:
        """Obtenir l'action du défenseur"""
        # Basé sur la personnalité
        bravery = defender.personality.get_trait(PersonalityTrait.BRAVE)
        
        # Plus l'agent est brave, plus il a de chances de contrer
        if random.random() < bravery:
            return CombatAction(
                action_type="attack",
                attacker_id=defender.agent_id,
                target_id=attacker.agent_id,
                damage=defender.attack_power * 0.8,  # Contre-attaque moins puissante
                accuracy=0.7
            )
        else:
            # Sinon, se défendre
            return CombatAction(
                action_type="defend",
                attacker_id=defender.agent_id,
                target_id=attacker.agent_id
            )
    
    def _check_retreat(self, agent: AIAgent, opponent: AIAgent) -> bool:
        """Vérifier si un agent doit battre en retraite"""
        # Basé sur la santé et la personnalité
        health_percent = agent.health / agent.max_health
        cautiousness = agent.personality.get_trait(PersonalityTrait.CAUTIOUS)
        
        # Si la santé est basse et que l'agent est prudent, fuir
        if health_percent < 0.3 and random.random() < cautiousness:
            return True
        
        # Si l'opponent est beaucoup plus fort
        strength_ratio = agent.attack_power / opponent.attack_power
        if strength_ratio < 0.5 and random.random() < 0.3:
            return True
        
        return False


class CombatSystem:
    """
    Système de combat pour AI World.
    Gère les combats entre agents.
    """
    
    def __init__(self):
        """Initialiser le système de combat"""
        self.logger = Logger("CombatSystem")
        
        # Combats en cours
        self.combats: Dict[str, Combat] = {}
        self.combat_counter = 0
        
        # Historique des combats
        self.combat_history: List[Combat] = []
        
        # Statistiques
        self.stats = {
            "combats_started": 0,
            "combats_ended": 0,
            "victories": 0,
            "defeats": 0,
            "draws": 0,
            "retreats": 0
        }
    
    def start_combat(self, attacker: AIAgent, defender: AIAgent,
                     combat_type: CombatType = CombatType.MELEE) -> Combat:
        """Démarrer un nouveau combat"""
        combat_id = f"combat_{self.combat_counter}"
        self.combat_counter += 1
        
        combat = Combat(
            combat_id=combat_id,
            attacker_id=attacker.agent_id,
            defender_id=defender.agent_id,
            combat_type=combat_type
        )
        
        self.combats[combat_id] = combat
        
        # Statistiques
        self.stats["combats_started"] += 1
        
        # Démarrer le combat
        combat.start()
        
        # Mettre à jour l'état des agents
        attacker.state = AgentState.FIGHTING
        defender.state = AgentState.FIGHTING
        
        self.logger.info(f"Combat démarré: {attacker.name} vs {defender.name}")
        
        return combat
    
    def update_combats(self):
        """Mettre à jour tous les combats"""
        # Faire une copie de la liste pour éviter les problèmes de modification
        combat_ids = list(self.combats.keys())
        
        for combat_id in combat_ids:
            combat = self.combats[combat_id]
            
            if combat.status == CombatStatus.ACTIVE:
                # Trouver les agents
                attacker = self._find_agent(combat.attacker_id)
                defender = self._find_agent(combat.defender_id)
                
                if not attacker or not defender:
                    # Un des agents n'existe plus
                    combat.end(CombatResult.DEFEAT)
                    self._cleanup_combat(combat_id)
                    continue
                
                # Effectuer un round
                if not combat.perform_round(attacker, defender):
                    self._cleanup_combat(combat_id)
    
    def _cleanup_combat(self, combat_id: str):
        """Nettoyer après un combat"""
        if combat_id not in self.combats:
            return
        
        combat = self.combats[combat_id]
        
        # Mettre à jour les statistiques
        self.stats["combats_ended"] += 1
        
        if combat.result == CombatResult.VICTORY:
            self.stats["victories"] += 1
        elif combat.result == CombatResult.DEFEAT:
            self.stats["defeats"] += 1
        elif combat.result == CombatResult.DRAW:
            self.stats["draws"] += 1
        elif combat.result == CombatResult.RETREAT:
            self.stats["retreats"] += 1
        
        # Ajouter à l'historique
        self.combat_history.append(combat)
        
        # Supprimer le combat
        del self.combats[combat_id]
        
        # Mettre à jour l'état des agents
        if combat.winner_id:
            winner = self._find_agent(combat.winner_id)
            if winner:
                winner.state = AgentState.IDLE
                # Expérience de victoire
                winner.personality.evolve({"won_fight": 1.0})
        
        if combat.loser_id:
            loser = self._find_agent(combat.loser_id)
            if loser:
                loser.state = AgentState.IDLE
                # Expérience de défaite
                loser.personality.evolve({"lost_fight": 1.0})
        
        self.logger.info(f"Combat terminé: {combat.combat_id} ({combat.result.name})")
    
    def _find_agent(self, agent_id: str) -> Optional[AIAgent]:
        """Trouver un agent (à implémenter dans la simulation)"""
        # Dans une implémentation complète, on chercherait dans la liste des agents
        return None
    
    def get_combat(self, combat_id: str) -> Optional[Combat]:
        """Obtenir un combat"""
        return self.combats.get(combat_id)
    
    def get_combats_by_agent(self, agent_id: str) -> List[Combat]:
        """Obtenir les combats impliquant un agent"""
        return [
            c for c in self.combats.values()
            if c.attacker_id == agent_id or c.defender_id == agent_id
        ]
    
    def get_combat_history(self, agent_id: str = None, limit: int = 100) -> List[Combat]:
        """Obtenir l'historique des combats"""
        if agent_id:
            return [
                c for c in self.combat_history
                if c.attacker_id == agent_id or c.defender_id == agent_id
            ][-limit:]
        return self.combat_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du système"""
        return {
            **self.stats,
            "active_combats": len(self.combats),
            "total_combats": len(self.combat_history)
        }
    
    def clear(self):
        """Effacer tous les combats"""
        self.combats.clear()
        self.combat_history.clear()
        self.stats = {
            "combats_started": 0,
            "combats_ended": 0,
            "victories": 0,
            "defeats": 0,
            "draws": 0,
            "retreats": 0
        }
    
    def start_group_combat(self, group1_id: str, group2_id: str) -> List[Combat]:
        """Démarrer des combats entre deux groupes"""
        # Trouver les membres des groupes
        group1_members = self._get_group_members(group1_id)
        group2_members = self._get_group_members(group2_id)
        
        if not group1_members or not group2_members:
            return []
        
        # Créer des combats entre les membres
        combats = []
        
        # Pour l'instant, créer un combat par paire
        for attacker in group1_members[:min(5, len(group1_members))]:
            for defender in group2_members[:min(5, len(group2_members))]:
                combat = self.start_combat(attacker, defender)
                combats.append(combat)
        
        return combats
    
    def _get_group_members(self, group_id: str) -> List[AIAgent]:
        """Obtenir les membres d'un groupe (à implémenter)"""
        return []
