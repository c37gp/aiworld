"""
Classe KnowledgeSystem - Système de connaissance pour AI World
"""

import random
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict

from ..config import config
from ..utils.logger import Logger
from ..agents.ai_agent import AIAgent


class KnowledgeType(Enum):
    """Types de connaissances"""
    FACT = auto()          # Fait
    SKILL = auto()         # Compétence
    RECIPE = auto()        # Recette
    LOCATION = auto()      # Localisation
    HISTORY = auto()       # Histoire
    RULE = auto()          # Règle
    STRATEGY = auto()      # Stratégie
    LANGUAGE = auto()      # Langue


class KnowledgeLevel(Enum):
    """Niveaux de connaissance"""
    UNKNOWN = auto()       # Inconnu
    HEARD = auto()         # Entendu parler
    BASIC = auto()         # Basique
    INTERMEDIATE = auto()  # Intermédiaire
    ADVANCED = auto()      # Avancé
    MASTER = auto()        # Maître


@dataclass
class Knowledge:
    """Représente une connaissance"""
    knowledge_id: str
    topic: str
    content: Any
    knowledge_type: KnowledgeType = KnowledgeType.FACT
    level: KnowledgeLevel = KnowledgeLevel.BASIC
    
    # Source et propagation
    creator_id: str = ""
    sources: List[str] = field(default_factory=list)  # IDs des agents sources
    
    # Confiance et utilité
    confidence: float = 0.5  # Niveau de confiance (0-1)
    usefulness: float = 0.5  # Utilité (0-1)
    
    # Statistiques
    times_shared: int = 0
    times_used: int = 0
    
    def improve(self, amount: float = 0.1):
        """Améliorer le niveau de connaissance"""
        levels = list(KnowledgeLevel)
        current_index = levels.index(self.level)
        
        # Augmenter la confiance
        self.confidence = min(1.0, self.confidence + amount * 0.5)
        
        # Passer au niveau supérieur si la confiance est suffisante
        if self.confidence >= 0.8 and current_index < len(levels) - 1:
            self.level = levels[current_index + 1]
    
    def use(self):
        """Utiliser la connaissance"""
        self.times_used += 1
        self.usefulness = min(1.0, self.usefulness + 0.01)
    
    def share(self, agent_id: str):
        """Partager la connaissance avec un agent"""
        self.times_shared += 1
        if agent_id not in self.sources:
            self.sources.append(agent_id)


@dataclass
class Skill:
    """Représente une compétence"""
    skill_id: str
    name: str
    description: str
    level: KnowledgeLevel = KnowledgeLevel.BASIC
    experience: float = 0.0
    
    # Bonus
    efficiency_bonus: float = 0.0
    quality_bonus: float = 0.0
    
    def gain_experience(self, amount: float):
        """Gagner de l'expérience"""
        self.experience += amount
        
        # Passer au niveau supérieur
        thresholds = {
            KnowledgeLevel.BASIC: 100,
            KnowledgeLevel.INTERMEDIATE: 300,
            KnowledgeLevel.ADVANCED: 600,
            KnowledgeLevel.MASTER: 1000
        }
        
        if self.level != KnowledgeLevel.MASTER:
            if self.experience >= thresholds.get(self.level, float('inf')):
                levels = list(KnowledgeLevel)
                current_index = levels.index(self.level)
                if current_index < len(levels) - 1:
                    self.level = levels[current_index + 1]
                    self.efficiency_bonus += 0.1
                    self.quality_bonus += 0.05
    
    def get_efficiency(self) -> float:
        """Obtenir l'efficacité de la compétence"""
        base = {
            KnowledgeLevel.UNKNOWN: 0.0,
            KnowledgeLevel.HEARD: 0.1,
            KnowledgeLevel.BASIC: 0.5,
            KnowledgeLevel.INTERMEDIATE: 0.8,
            KnowledgeLevel.ADVANCED: 1.0,
            KnowledgeLevel.MASTER: 1.2
        }
        return base.get(self.level, 0.5) + self.efficiency_bonus


@dataclass
class Recipe:
    """Représente une recette"""
    recipe_id: str
    name: str
    input_resources: Dict[str, float]  # Ressources nécessaires
    output_resources: Dict[str, float]  # Ressources produites
    required_skills: List[str] = field(default_factory=list)
    required_level: KnowledgeLevel = KnowledgeLevel.BASIC
    
    # Efficacité
    efficiency: float = 1.0
    
    def can_craft(self, inventory: Dict[str, float], skills: Dict[str, KnowledgeLevel]) -> bool:
        """Vérifier si on peut fabriquer"""
        # Vérifier les ressources
        for resource, amount in self.input_resources.items():
            if inventory.get(resource, 0) < amount:
                return False
        
        # Vérifier les compétences
        for skill_id in self.required_skills:
            if skill_id not in skills:
                return False
            if skills[skill_id].value < self.required_level.value:
                return False
        
        return True
    
    def craft(self, inventory: Dict[str, float]) -> Dict[str, float]:
        """Fabriquer, retourne les ressources produites"""
        if not self.can_craft(inventory):
            return {}
        
        # Consommer les ressources
        for resource, amount in self.input_resources.items():
            inventory[resource] = inventory.get(resource, 0) - amount
        
        # Produire les ressources
        produced = {}
        for resource, amount in self.output_resources.items():
            produced[resource] = amount * self.efficiency
        
        return produced


class KnowledgeSystem:
    """
    Système de connaissance pour AI World.
    Gère la création, le partage et l'utilisation des connaissances.
    """
    
    def __init__(self):
        """Initialiser le système de connaissance"""
        self.logger = Logger("KnowledgeSystem")
        
        # Base de connaissances globale
        self.knowledge_base: Dict[str, Knowledge] = {}
        
        # Compétences
        self.skills: Dict[str, Skill] = {}
        
        # Recettes
        self.recipes: Dict[str, Recipe] = {}
        
        # Connaissances par agent
        self.agent_knowledge: Dict[str, Set[str]] = defaultdict(set)
        
        # Statistiques
        self.stats = {
            "total_knowledge": 0,
            "total_skills": 0,
            "total_recipes": 0,
            "knowledge_shared": 0,
            "knowledge_created": 0
        }
        
        # Initialiser les connaissances de base
        self._initialize_base_knowledge()
    
    def _initialize_base_knowledge(self):
        """Initialiser les connaissances de base"""
        # Ajouter quelques compétences de base
        self.add_skill(Skill(
            skill_id="gathering",
            name="Récolte",
            description="Capacité à récolter des ressources efficacement"
        ))
        
        self.add_skill(Skill(
            skill_id="building",
            name="Construction",
            description="Capacité à construire des structures"
        ))
        
        self.add_skill(Skill(
            skill_id="fighting",
            name="Combat",
            description="Capacité à combattre"
        ))
        
        self.add_skill(Skill(
            skill_id="trading",
            name="Commerce",
            description="Capacité à négocier"
        ))
        
        # Ajouter quelques recettes de base
        self.add_recipe(Recipe(
            recipe_id="wood_to_tools",
            name="Fabrication d'outils en bois",
            input_resources={"wood": 10},
            output_resources={"tools": 1}
        ))
        
        self.add_recipe(Recipe(
            recipe_id="stone_to_building",
            name="Construction en pierre",
            input_resources={"stone": 20},
            output_resources={"building_materials": 1}
        ))
    
    def add_knowledge(self, knowledge: Knowledge) -> bool:
        """Ajouter une connaissance"""
        if knowledge.knowledge_id in self.knowledge_base:
            return False
        
        self.knowledge_base[knowledge.knowledge_id] = knowledge
        self.stats["total_knowledge"] += 1
        self.stats["knowledge_created"] += 1
        
        self.logger.debug(f"Connaissance ajoutée: {knowledge.topic}")
        
        return True
    
    def add_skill(self, skill: Skill) -> bool:
        """Ajouter une compétence"""
        if skill.skill_id in self.skills:
            return False
        
        self.skills[skill.skill_id] = skill
        self.stats["total_skills"] += 1
        
        return True
    
    def add_recipe(self, recipe: Recipe) -> bool:
        """Ajouter une recette"""
        if recipe.recipe_id in self.recipes:
            return False
        
        self.recipes[recipe.recipe_id] = recipe
        self.stats["total_recipes"] += 1
        
        return True
    
    def learn_knowledge(self, agent_id: str, knowledge_id: str, 
                        confidence: float = 0.5) -> bool:
        """Apprendre une connaissance"""
        if knowledge_id not in self.knowledge_base:
            return False
        
        # Ajouter à la liste des connaissances de l'agent
        self.agent_knowledge[agent_id].add(knowledge_id)
        
        # Mettre à jour la confiance
        knowledge = self.knowledge_base[knowledge_id]
        knowledge.confidence = max(knowledge.confidence, confidence)
        
        self.logger.debug(f"{agent_id} a appris: {knowledge.topic}")
        
        return True
    
    def learn_skill(self, agent_id: str, skill_id: str) -> bool:
        """Apprendre une compétence"""
        if skill_id not in self.skills:
            return False
        
        # Pour l'instant, on ne fait que noter que l'agent a la compétence
        # Dans une version avancée, on gérera les niveaux par agent
        return True
    
    def share_knowledge(self, from_agent: AIAgent, to_agent: AIAgent, 
                        knowledge_id: str = None) -> bool:
        """Partager une connaissance entre agents"""
        if knowledge_id:
            # Partager une connaissance spécifique
            if knowledge_id not in self.knowledge_base:
                return False
            
            knowledge = self.knowledge_base[knowledge_id]
            
            # Vérifier si l'agent source connaît cette connaissance
            if knowledge_id not in self.agent_knowledge.get(from_agent.agent_id, set()):
                return False
            
            # Apprendre la connaissance
            to_agent.memory.add_knowledge(
                topic=knowledge.topic,
                content=knowledge.content,
                source=from_agent.agent_id,
                confidence=knowledge.confidence * 0.9  # Légère perte de confiance
            )
            
            # Mettre à jour les statistiques
            knowledge.share(from_agent.agent_id)
            from_agent.stats.knowledge_shared += 1
            to_agent.stats.knowledge_received += 1
            self.stats["knowledge_shared"] += 1
            
            # Ajouter à la liste des connaissances de l'agent cible
            self.agent_knowledge[to_agent.agent_id].add(knowledge_id)
            
            self.logger.debug(f"Connaissance partagée: {from_agent.name} -> {to_agent.name} ({knowledge.topic})")
            
            return True
        else:
            # Partager une connaissance aléatoire
            from_knowledge = self.get_agent_knowledge(from_agent.agent_id)
            if not from_knowledge:
                return False
            
            knowledge_id = random.choice(from_knowledge)
            return self.share_knowledge(from_agent, to_agent, knowledge_id)
    
    def create_knowledge(self, creator: AIAgent, topic: str, content: Any,
                         knowledge_type: KnowledgeType = KnowledgeType.FACT) -> Knowledge:
        """Créer une nouvelle connaissance"""
        knowledge_id = f"knowledge_{len(self.knowledge_base)}"
        
        knowledge = Knowledge(
            knowledge_id=knowledge_id,
            topic=topic,
            content=content,
            knowledge_type=knowledge_type,
            creator_id=creator.agent_id,
            confidence=0.7,  # Confiance initiale
            usefulness=0.5
        )
        
        self.add_knowledge(knowledge)
        
        # L'agent créateur apprend automatiquement la connaissance
        self.learn_knowledge(creator.agent_id, knowledge_id, 1.0)
        
        # Ajouter à la mémoire de l'agent
        creator.memory.add_knowledge(
            topic=topic,
            content=content,
            source=creator.agent_id,
            confidence=1.0
        )
        
        self.logger.info(f"Nouvelle connaissance créée: {topic} par {creator.name}")
        
        return knowledge
    
    def discover_recipe(self, creator: AIAgent, name: str, 
                        input_resources: Dict[str, float], 
                        output_resources: Dict[str, float]) -> Recipe:
        """Découvrir une nouvelle recette"""
        recipe_id = f"recipe_{len(self.recipes)}"
        
        recipe = Recipe(
            recipe_id=recipe_id,
            name=name,
            input_resources=input_resources,
            output_resources=output_resources
        )
        
        self.add_recipe(recipe)
        
        # Créer une connaissance associée
        knowledge = self.create_knowledge(
            creator=creator,
            topic=f"Recette: {name}",
            content={"recipe_id": recipe_id, "name": name},
            knowledge_type=KnowledgeType.RECIPE
        )
        
        self.logger.info(f"Nouvelle recette découverte: {name} par {creator.name}")
        
        return recipe
    
    def get_knowledge(self, knowledge_id: str) -> Optional[Knowledge]:
        """Obtenir une connaissance"""
        return self.knowledge_base.get(knowledge_id)
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Obtenir une compétence"""
        return self.skills.get(skill_id)
    
    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """Obtenir une recette"""
        return self.recipes.get(recipe_id)
    
    def get_agent_knowledge(self, agent_id: str) -> List[Knowledge]:
        """Obtenir les connaissances d'un agent"""
        knowledge_ids = self.agent_knowledge.get(agent_id, set())
        return [self.knowledge_base[kid] for kid in knowledge_ids if kid in self.knowledge_base]
    
    def get_knowledge_by_topic(self, topic: str) -> List[Knowledge]:
        """Obtenir les connaissances par sujet"""
        return [k for k in self.knowledge_base.values() if k.topic.lower() == topic.lower()]
    
    def get_knowledge_by_type(self, knowledge_type: KnowledgeType) -> List[Knowledge]:
        """Obtenir les connaissances par type"""
        return [k for k in self.knowledge_base.values() if k.knowledge_type == knowledge_type]
    
    def get_recipes_by_input(self, resource_type: str) -> List[Recipe]:
        """Obtenir les recettes qui utilisent une ressource en entrée"""
        return [r for r in self.recipes.values() if resource_type in r.input_resources]
    
    def get_recipes_by_output(self, resource_type: str) -> List[Recipe]:
        """Obtenir les recettes qui produisent une ressource"""
        return [r for r in self.recipes.values() if resource_type in r.output_resources]
    
    def can_craft(self, agent_id: str, recipe_id: str) -> bool:
        """Vérifier si un agent peut fabriquer une recette"""
        if recipe_id not in self.recipes:
            return False
        
        recipe = self.recipes[recipe_id]
        
        # Pour l'instant, on vérifie seulement si l'agent connaît la recette
        # Dans une version avancée, on vérifierait aussi les compétences et ressources
        knowledge = self.get_knowledge(f"knowledge_{recipe_id}")
        if knowledge:
            return knowledge.knowledge_id in self.agent_knowledge.get(agent_id, set())
        
        return False
    
    def teach(self, teacher: AIAgent, student: AIAgent, knowledge_id: str) -> bool:
        """Enseigner une connaissance"""
        if knowledge_id not in self.knowledge_base:
            return False
        
        knowledge = self.knowledge_base[knowledge_id]
        
        # Vérifier si l'enseignant connaît cette connaissance
        if knowledge_id not in self.agent_knowledge.get(teacher.agent_id, set()):
            return False
        
        # Vérifier le niveau de l'enseignant
        teacher_level = self._get_agent_knowledge_level(teacher.agent_id, knowledge_id)
        if teacher_level < KnowledgeLevel.INTERMEDIATE:
            return False  # L'enseignant n'est pas assez compétent
        
        # Enseigner la connaissance
        return self.share_knowledge(teacher, student, knowledge_id)
    
    def _get_agent_knowledge_level(self, agent_id: str, knowledge_id: str) -> KnowledgeLevel:
        """Obtenir le niveau de connaissance d'un agent"""
        # Pour l'instant, retourner le niveau par défaut de la connaissance
        # Dans une version avancée, chaque agent aurait son propre niveau
        if knowledge_id in self.knowledge_base:
            return self.knowledge_base[knowledge_id].level
        return KnowledgeLevel.UNKNOWN
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du système"""
        return {
            **self.stats,
            "agents_with_knowledge": len(self.agent_knowledge),
            "average_knowledge_per_agent": sum(len(kn) for kn in self.agent_knowledge.values()) / max(1, len(self.agent_knowledge))
        }
    
    def clear(self):
        """Effacer toutes les connaissances"""
        self.knowledge_base.clear()
        self.skills.clear()
        self.recipes.clear()
        self.agent_knowledge.clear()
        self.stats = {
            "total_knowledge": 0,
            "total_skills": 0,
            "total_recipes": 0,
            "knowledge_shared": 0,
            "knowledge_created": 0
        }
