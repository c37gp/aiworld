"""
Classe SocialSystem - Système social pour les groupes et règles
"""

import random
import time
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict

from ..config import config
from ..utils.logger import Logger
from ..agents.ai_agent import AIAgent
from .communication import CommunicationSystem, Message, MessageType


class GroupType(Enum):
    """Types de groupes"""
    FAMILY = auto()        # Famille
    CLAN = auto()          # Clan
    TRIBE = auto()         # Tribu
    VILLAGE = auto()       # Village
    CITY = auto()          # Ville
    ALLIANCE = auto()      # Alliance
    GUILD = auto()         # Guilde
    ARMY = auto()          # Armée


class MemberRole(Enum):
    """Rôles dans un groupe"""
    LEADER = auto()        # Chef
    CO_LEADER = auto()     # Co-chef
    MEMBER = auto()        # Membre
    NEWBIE = auto()        # Nouveau
    ELDER = auto()         # Anciens
    GUARD = auto()         # Garde
    WORKER = auto()        # Travailleur
    SCOUT = auto()         # Éclaireur


class RuleType(Enum):
    """Types de règles"""
    LAW = auto()           # Loi
    NORM = auto()          # Norme
    TRADITION = auto()     # Tradition
    CUSTOM = auto()        # Coutume


@dataclass
class Rule:
    """Représente une règle dans un groupe"""
    rule_id: str
    name: str
    description: str
    rule_type: RuleType = RuleType.NORM
    creator_id: str = ""
    severity: float = 0.5  # Gravité (0-1)
    enforcement: float = 0.5  # Application (0-1)
    
    # Conditions et conséquences
    condition: Optional[Callable[[AIAgent, Any], bool]] = None
    consequence: Optional[Callable[[AIAgent], None]] = None
    
    # Statistiques
    violations: int = 0
    enforcements: int = 0
    
    def check_violation(self, agent: AIAgent, context: Any = None) -> bool:
        """Vérifier si un agent viole la règle"""
        if self.condition:
            return not self.condition(agent, context)
        return False
    
    def enforce(self, agent: AIAgent):
        """Appliquer la conséquence de la violation"""
        self.enforcements += 1
        if self.consequence:
            self.consequence(agent)


@dataclass
class Group:
    """Représente un groupe d'agents"""
    group_id: str
    name: str
    group_type: GroupType = GroupType.CLAN
    founder_id: str = ""
    creation_time: float = field(default_factory=lambda: time.time())
    
    # Membres
    members: Dict[str, MemberRole] = field(default_factory=dict)
    
    # Règles
    rules: Dict[str, Rule] = field(default_factory=dict)
    
    # Ressources du groupe
    shared_resources: Dict[str, float] = field(default_factory=dict)
    
    # Statistiques
    stats: Dict[str, Any] = field(default_factory=dict)
    
    # Position centrale (pour les groupes sédentaires)
    center_position: Optional[Any] = None  # Vector2
    
    # Territoire (pour les groupes avec territoire)
    territory_radius: float = 0.0
    
    def __post_init__(self):
        self.stats = {
            "total_members": 0,
            "resources_collected": 0,
            "structures_built": 0,
            "conflicts": 0
        }
    
    def add_member(self, agent_id: str, role: MemberRole = MemberRole.MEMBER) -> bool:
        """Ajouter un membre au groupe"""
        if agent_id in self.members:
            return False
        
        self.members[agent_id] = role
        self.stats["total_members"] += 1
        return True
    
    def remove_member(self, agent_id: str) -> bool:
        """Retirer un membre du groupe"""
        if agent_id not in self.members:
            return False
        
        del self.members[agent_id]
        self.stats["total_members"] -= 1
        
        # Si c'était le dernier membre, dissoudre le groupe
        if len(self.members) == 0:
            return True
        
        # Si c'était le leader, élire un nouveau leader
        if self.members.get(agent_id) == MemberRole.LEADER:
            self._elect_new_leader()
        
        return True
    
    def _elect_new_leader(self):
        """Élire un nouveau leader"""
        if not self.members:
            return
        
        # Pour l'instant, choisir le membre le plus ancien
        # Dans une version plus avancée, on organiserait une élection
        oldest_member = max(self.members.keys(), key=lambda x: x)  # Simplification
        self.members[oldest_member] = MemberRole.LEADER
    
    def get_leader(self) -> Optional[str]:
        """Obtenir l'ID du leader"""
        for agent_id, role in self.members.items():
            if role == MemberRole.LEADER:
                return agent_id
        return None
    
    def get_members(self) -> List[str]:
        """Obtenir la liste des membres"""
        return list(self.members.keys())
    
    def get_members_by_role(self, role: MemberRole) -> List[str]:
        """Obtenir les membres avec un rôle spécifique"""
        return [agent_id for agent_id, r in self.members.items() if r == role]
    
    def add_rule(self, rule: Rule) -> bool:
        """Ajouter une règle"""
        if rule.rule_id in self.rules:
            return False
        
        self.rules[rule.rule_id] = rule
        return True
    
    def remove_rule(self, rule_id: str) -> bool:
        """Supprimer une règle"""
        if rule_id not in self.rules:
            return False
        
        del self.rules[rule_id]
        return True
    
    def check_rules(self, agent_id: str, context: Any = None) -> List[Rule]:
        """Vérifier quelles règles sont violées par un agent"""
        violations = []
        
        for rule in self.rules.values():
            if rule.check_violation(agent_id, context):
                violations.append(rule)
        
        return violations
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Obtenir une règle"""
        return self.rules.get(rule_id)
    
    def add_resource(self, resource_type: str, amount: float):
        """Ajouter une ressource au groupe"""
        self.shared_resources[resource_type] = self.shared_resources.get(resource_type, 0) + amount
        self.stats["resources_collected"] += amount
    
    def remove_resource(self, resource_type: str, amount: float) -> float:
        """Retirer une ressource du groupe"""
        current = self.shared_resources.get(resource_type, 0)
        removed = min(amount, current)
        self.shared_resources[resource_type] = current - removed
        return removed
    
    def get_resource(self, resource_type: str) -> float:
        """Obtenir la quantité d'une ressource"""
        return self.shared_resources.get(resource_type, 0)
    
    def set_center_position(self, position):
        """Définir la position centrale du groupe"""
        self.center_position = position
    
    def set_territory(self, center, radius: float):
        """Définir le territoire du groupe"""
        self.center_position = center
        self.territory_radius = radius
    
    def is_in_territory(self, position) -> bool:
        """Vérifier si une position est dans le territoire"""
        if not self.center_position:
            return False
        
        distance = self.center_position.distance_to(position)
        return distance <= self.territory_radius


class SocialSystem:
    """
    Système social pour la gestion des groupes et règles.
    """
    
    def __init__(self, communication_system: CommunicationSystem = None):
        """Initialiser le système social"""
        self.logger = Logger("SocialSystem")
        self.communication = communication_system
        
        # Groupes
        self.groups: Dict[str, Group] = {}
        self.group_counter = 0
        
        # Agents et leurs groupes
        self.agent_groups: Dict[str, str] = {}  # agent_id -> group_id
        
        # Relations entre groupes
        self.group_relations: Dict[Tuple[str, str], str] = {}  # (group1, group2) -> relation
        
        # Événements sociaux
        self.events: List[Dict[str, Any]] = []
        
        # Statistiques
        self.stats = {
            "total_groups": 0,
            "total_members": 0,
            "elections": 0,
            "rules_created": 0,
            "conflicts": 0
        }
    
    def create_group(self, founder: AIAgent, name: str, 
                     group_type: GroupType = GroupType.CLAN) -> Group:
        """Créer un nouveau groupe"""
        group_id = f"group_{self.group_counter}"
        self.group_counter += 1
        
        group = Group(
            group_id=group_id,
            name=name,
            group_type=group_type,
            founder_id=founder.agent_id
        )
        
        # Ajouter le fondateur comme leader
        group.add_member(founder.agent_id, MemberRole.LEADER)
        
        # Enregistrer le groupe
        self.groups[group_id] = group
        self.agent_groups[founder.agent_id] = group_id
        
        # Mettre à jour les statistiques
        self.stats["total_groups"] += 1
        self.stats["total_members"] += 1
        
        # Faire rejoindre le groupe au fondateur
        founder.join_group(group_id, founder.agent_id)
        
        self.logger.info(f"Groupe créé: {name} (ID: {group_id})")
        
        return group
    
    def dissolve_group(self, group_id: str) -> bool:
        """Dissoudre un groupe"""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        
        # Notifier les membres
        for agent_id in group.get_members():
            if agent_id in self.agent_groups:
                del self.agent_groups[agent_id]
        
        # Supprimer le groupe
        del self.groups[group_id]
        
        # Mettre à jour les statistiques
        self.stats["total_groups"] -= 1
        self.stats["total_members"] -= len(group.members)
        
        self.logger.info(f"Groupe dissous: {group.name}")
        
        return True
    
    def join_group(self, agent: AIAgent, group_id: str) -> bool:
        """Faire rejoindre un groupe à un agent"""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        
        # Vérifier si l'agent peut rejoindre
        # (dans une version avancée, on vérifierait les conditions d'adhésion)
        
        # Ajouter au groupe
        success = group.add_member(agent.agent_id)
        
        if success:
            self.agent_groups[agent.agent_id] = group_id
            agent.join_group(group_id)
            self.stats["total_members"] += 1
            
            self.logger.info(f"{agent.name} a rejoint {group.name}")
            
            # Notifier le groupe
            if self.communication:
                self.communication.broadcast(
                    agent,
                    f"{agent.name} a rejoint le groupe!",
                    MessageType.TEXT
                )
        
        return success
    
    def leave_group(self, agent: AIAgent) -> bool:
        """Faire quitter un groupe à un agent"""
        if agent.agent_id not in self.agent_groups:
            return False
        
        group_id = self.agent_groups[agent.agent_id]
        group = self.groups.get(group_id)
        
        if group:
            success = group.remove_member(agent.agent_id)
            
            if success:
                del self.agent_groups[agent.agent_id]
                agent.leave_group()
                self.stats["total_members"] -= 1
                
                self.logger.info(f"{agent.name} a quitté {group.name}")
                
                # Notifier le groupe
                if self.communication:
                    self.communication.broadcast(
                        agent,
                        f"{agent.name} a quitté le groupe.",
                        MessageType.TEXT
                    )
            
            return success
        
        return False
    
    def get_agent_group(self, agent_id: str) -> Optional[Group]:
        """Obtenir le groupe d'un agent"""
        if agent_id not in self.agent_groups:
            return None
        
        group_id = self.agent_groups[agent_id]
        return self.groups.get(group_id)
    
    def get_group(self, group_id: str) -> Optional[Group]:
        """Obtenir un groupe"""
        return self.groups.get(group_id)
    
    def elect_leader(self, group_id: str, candidates: List[str] = None) -> Optional[str]:
        """Élire un nouveau leader pour un groupe"""
        if group_id not in self.groups:
            return None
        
        group = self.groups[group_id]
        
        # Si des candidats sont spécifiés, utiliser ceux-là
        if candidates:
            eligible = candidates
        else:
            # Tous les membres peuvent être candidats
            eligible = group.get_members()
        
        # Pour l'instant, choisir aléatoirement
        # Dans une version avancée, on organiserait un vote
        new_leader = random.choice(eligible)
        
        # Mettre à jour les rôles
        for member_id in group.members:
            if member_id == new_leader:
                group.members[member_id] = MemberRole.LEADER
            elif group.members[member_id] == MemberRole.LEADER:
                group.members[member_id] = MemberRole.MEMBER
        
        self.stats["elections"] += 1
        
        self.logger.info(f"Nouveau leader élu pour {group.name}: {new_leader}")
        
        return new_leader
    
    def create_rule(self, creator: AIAgent, name: str, description: str,
                    rule_type: RuleType = RuleType.NORM, 
                    severity: float = 0.5, 
                    enforcement: float = 0.5) -> Optional[Rule]:
        """Créer une nouvelle règle"""
        # Vérifier que l'agent est dans un groupe et est leader
        group = self.get_agent_group(creator.agent_id)
        
        if not group or group.get_leader() != creator.agent_id:
            self.logger.warning(f"{creator.name} ne peut pas créer de règle (n'est pas leader)")
            return None
        
        rule_id = f"rule_{len(group.rules)}"
        
        rule = Rule(
            rule_id=rule_id,
            name=name,
            description=description,
            rule_type=rule_type,
            creator_id=creator.agent_id,
            severity=severity,
            enforcement=enforcement
        )
        
        # Ajouter la règle au groupe
        group.add_rule(rule)
        
        # Statistiques
        self.stats["rules_created"] += 1
        
        # Notifier le groupe
        if self.communication:
            self.communication.broadcast(
                creator,
                f"Nouvelle règle: {name} - {description}",
                MessageType.TEXT
            )
        
        self.logger.info(f"Règle créée: {name} (groupe: {group.name})")
        
        return rule
    
    def enforce_rules(self, agent: AIAgent, context: Any = None) -> List[Rule]:
        """Appliquer les règles pour un agent"""
        group = self.get_agent_group(agent.agent_id)
        
        if not group:
            return []
        
        # Vérifier les violations
        violations = group.check_rules(agent.agent_id, context)
        
        # Appliquer les conséquences
        for rule in violations:
            rule.enforce(agent)
            
            # Notifier
            if self.communication:
                self.communication.broadcast(
                    agent,
                    f"{agent.name} a violé la règle: {rule.name}",
                    MessageType.WARNING
                )
        
        return violations
    
    def set_group_relation(self, group1_id: str, group2_id: str, relation: str) -> bool:
        """Définir la relation entre deux groupes"""
        if group1_id not in self.groups or group2_id not in self.groups:
            return False
        
        key = (group1_id, group2_id) if group1_id < group2_id else (group2_id, group1_id)
        self.group_relations[key] = relation
        
        self.logger.info(f"Relation définie: {group1_id} <-> {group2_id} = {relation}")
        
        return True
    
    def get_group_relation(self, group1_id: str, group2_id: str) -> Optional[str]:
        """Obtenir la relation entre deux groupes"""
        key = (group1_id, group2_id) if group1_id < group2_id else (group2_id, group1_id)
        return self.group_relations.get(key)
    
    def form_alliance(self, group1_id: str, group2_id: str) -> bool:
        """Former une alliance entre deux groupes"""
        return self.set_group_relation(group1_id, group2_id, "alliance")
    
    def declare_war(self, group1_id: str, group2_id: str) -> bool:
        """Déclarer la guerre entre deux groupes"""
        return self.set_group_relation(group1_id, group2_id, "war")
    
    def make_peace(self, group1_id: str, group2_id: str) -> bool:
        """Faire la paix entre deux groupes"""
        return self.set_group_relation(group1_id, group2_id, "peace")
    
    def get_all_groups(self) -> List[Group]:
        """Obtenir tous les groupes"""
        return list(self.groups.values())
    
    def get_groups_by_type(self, group_type: GroupType) -> List[Group]:
        """Obtenir les groupes d'un type spécifique"""
        return [g for g in self.groups.values() if g.group_type == group_type]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du système social"""
        return {
            **self.stats,
            "groups": len(self.groups),
            "group_relations": len(self.group_relations),
            "largest_group": max([len(g.members) for g in self.groups.values()], default=0)
        }
    
    def update(self, delta_time: float):
        """Mettre à jour le système social"""
        # Pour l'instant, rien à faire
        pass
    
    def clear(self):
        """Effacer tous les groupes"""
        self.groups.clear()
        self.agent_groups.clear()
        self.group_relations.clear()
        self.stats = {
            "total_groups": 0,
            "total_members": 0,
            "elections": 0,
            "rules_created": 0,
            "conflicts": 0
        }
