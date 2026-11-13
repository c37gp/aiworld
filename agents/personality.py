"""
Classe AgentPersonality - Gestion de la personnalité des agents
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto


class PersonalityTrait(Enum):
    """Traits de personnalité"""
    CURIOUS = auto()      # Curiosité
    AGGRESSIVE = auto()   # Agressivité
    SOCIABLE = auto()     # Sociabilité
    INTELLIGENT = auto()  # Intelligence
    CREATIVE = auto()     # Créativité
    LOYAL = auto()         # Loyauté
    AMBITIOUS = auto()    # Ambition
    PEACEFUL = auto()     # Pacifique
    BRAVE = auto()         # Courageux
    CAUTIOUS = auto()     # Prudent


@dataclass
class Trait:
    """Représente un trait de personnalité"""
    trait_type: PersonalityTrait
    value: float  # Entre 0 et 1
    
    def __post_init__(self):
        self.value = max(0, min(1, self.value))


@dataclass
class PersonalityProfile:
    """Profil de personnalité complet"""
    traits: Dict[PersonalityTrait, float] = field(default_factory=dict)
    
    def get_trait(self, trait: PersonalityTrait) -> float:
        """Obtenir la valeur d'un trait"""
        return self.traits.get(trait, 0.5)
    
    def set_trait(self, trait: PersonalityTrait, value: float):
        """Définir la valeur d'un trait"""
        self.traits[trait] = max(0, min(1, value))
    
    def modify_trait(self, trait: PersonalityTrait, delta: float):
        """Modifier la valeur d'un trait"""
        current = self.get_trait(trait)
        self.set_trait(trait, current + delta)
    
    def get_opposites(self) -> Dict[str, float]:
        """Obtenir les traits opposés"""
        opposites = {
            PersonalityTrait.AGGRESSIVE: PersonalityTrait.PEACEFUL,
            PersonalityTrait.PEACEFUL: PersonalityTrait.AGGRESSIVE,
            PersonalityTrait.BRAVE: PersonalityTrait.CAUTIOUS,
            PersonalityTrait.CAUTIOUS: PersonalityTrait.BRAVE,
            PersonalityTrait.SOCIABLE: PersonalityTrait.CURIOUS,  # Pas exactement opposé mais différent
            PersonalityTrait.LOYAL: PersonalityTrait.AMBITIOUS
        }
        
        result = {}
        for trait, opposite in opposites.items():
            result[trait.name] = self.get_trait(opposite)
        
        return result


class AgentPersonality:
    """
    Gère la personnalité d'un agent IA.
    Influence ses décisions et comportements.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialiser la personnalité"""
        self.seed = seed or random.randint(0, 1000000)
        random.seed(self.seed)
        
        self.profile = PersonalityProfile()
        self._generate_personality()
        
        # Compatibilité avec d'autres agents
        self.compatibility_cache: Dict[str, float] = {}
    
    def _generate_personality(self):
        """Générer une personnalité aléatoire"""
        # Traits de base
        traits = [
            PersonalityTrait.CURIOUS,
            PersonalityTrait.AGGRESSIVE,
            PersonalityTrait.SOCIABLE,
            PersonalityTrait.INTELLIGENT,
            PersonalityTrait.CREATIVE,
            PersonalityTrait.LOYAL,
            PersonalityTrait.AMBITIOUS,
            PersonalityTrait.PEACEFUL,
            PersonalityTrait.BRAVE,
            PersonalityTrait.CAUTIOUS
        ]
        
        for trait in traits:
            # Générer une valeur aléatoire avec une distribution normale centrée sur 0.5
            value = random.gauss(0.5, 0.2)
            self.profile.set_trait(trait, value)
        
        # Assurer que les opposés sont cohérents
        self._ensure_consistency()
    
    def _ensure_consistency(self):
        """Assurer la cohérence entre les traits opposés"""
        # Agressif vs Pacifique
        aggressive = self.profile.get_trait(PersonalityTrait.AGGRESSIVE)
        peaceful = self.profile.get_trait(PersonalityTrait.PEACEFUL)
        if aggressive > 0.7 and peaceful > 0.7:
            # Les deux ne peuvent pas être élevés
            if random.random() > 0.5:
                self.profile.set_trait(PersonalityTrait.AGGRESSIVE, 1 - peaceful)
            else:
                self.profile.set_trait(PersonalityTrait.PEACEFUL, 1 - aggressive)
        
        # Brave vs Prudent
        brave = self.profile.get_trait(PersonalityTrait.BRAVE)
        cautious = self.profile.get_trait(PersonalityTrait.CAUTIOUS)
        if brave > 0.7 and cautious > 0.7:
            if random.random() > 0.5:
                self.profile.set_trait(PersonalityTrait.BRAVE, 1 - cautious)
            else:
                self.profile.set_trait(PersonalityTrait.CAUTIOUS, 1 - brave)
    
    def get_trait(self, trait: PersonalityTrait) -> float:
        """Obtenir la valeur d'un trait"""
        return self.profile.get_trait(trait)
    
    def get_all_traits(self) -> Dict[str, float]:
        """Obtenir tous les traits"""
        return {trait.name: self.profile.get_trait(trait) for trait in PersonalityTrait}
    
    def get_personality_summary(self) -> str:
        """Obtenir un résumé de la personnalité"""
        dominant_traits = []
        for trait in PersonalityTrait:
            value = self.get_trait(trait)
            if value > 0.7:
                dominant_traits.append(trait.name.lower())
        
        if dominant_traits:
            return ", ".join(dominant_traits)
        return "équilibrée"
    
    def get_decision_influence(self, decision_type: str) -> float:
        """
        Obtenir l'influence de la personnalité sur un type de décision.
        Retourne un multiplicateur entre 0 et 2.
        """
        influences = {
            "explore": self.get_trait(PersonalityTrait.CURIOUS) * 2,
            "fight": self.get_trait(PersonalityTrait.AGGRESSIVE) * 2,
            "flee": (1 - self.get_trait(PersonalityTrait.BRAVE)) * 2,
            "socialize": self.get_trait(PersonalityTrait.SOCIABLE) * 2,
            "trade": (self.get_trait(PersonalityTrait.INTELLIGENT) + 
                      self.get_trait(PersonalityTrait.SOCIABLE)) / 2 * 2,
            "build": (self.get_trait(PersonalityTrait.CREATIVE) + 
                      self.get_trait(PersonalityTrait.INTELLIGENT)) / 2 * 2,
            "lead": (self.get_trait(PersonalityTrait.AMBITIOUS) + 
                     self.get_trait(PersonalityTrait.INTELLIGENT)) / 2 * 2,
            "follow": self.get_trait(PersonalityTrait.LOYAL) * 2,
            "help": (self.get_trait(PersonalityTrait.LOYAL) + 
                     self.get_trait(PersonalityTrait.PEACEFUL)) / 2 * 2,
            "steal": self.get_trait(PersonalityTrait.AGGRESSIVE) * 
                     (1 - self.get_trait(PersonalityTrait.LOYAL)) * 2
        }
        
        return influences.get(decision_type, 1.0)
    
    def calculate_compatibility(self, other_personality: "AgentPersonality") -> float:
        """
        Calculer la compatibilité avec une autre personnalité.
        Retourne une valeur entre 0 et 1.
        """
        # Utiliser le cache si disponible
        other_id = str(id(other_personality))
        if other_id in self.compatibility_cache:
            return self.compatibility_cache[other_id]
        
        # Calculer la compatibilité
        compatibility = 0.0
        total_traits = 0
        
        for trait in PersonalityTrait:
            my_value = self.get_trait(trait)
            other_value = other_personality.get_trait(trait)
            
            # Plus les valeurs sont proches, plus la compatibilité est élevée
            diff = abs(my_value - other_value)
            trait_compatibility = 1 - diff
            
            compatibility += trait_compatibility
            total_traits += 1
        
        if total_traits > 0:
            compatibility /= total_traits
        
        # Ajouter un bonus pour les traits complémentaires
        my_aggressive = self.get_trait(PersonalityTrait.AGGRESSIVE)
        other_peaceful = other_personality.get_trait(PersonalityTrait.PEACEFUL)
        
        my_peaceful = self.get_trait(PersonalityTrait.PEACEFUL)
        other_aggressive = other_personality.get_trait(PersonalityTrait.AGGRESSIVE)
        
        # Si un est agressif et l'autre pacifique, c'est complémentaire
        complementarity = (my_aggressive * other_peaceful + 
                          my_peaceful * other_aggressive) * 0.5
        
        compatibility = (compatibility * 0.7 + complementarity * 0.3)
        
        # Mettre en cache
        self.compatibility_cache[other_id] = compatibility
        other_personality.compatibility_cache[str(id(self))] = compatibility
        
        return compatibility
    
    def evolve(self, experience: Dict[str, float]):
        """
        Faire évoluer la personnalité en fonction des expériences.
        Les expériences sont des événements qui ont influencé l'agent.
        """
        # Exemples d'expériences : "won_fight", "lost_fight", "made_friend", etc.
        for event, intensity in experience.items():
            if event == "won_fight":
                self.profile.modify_trait(PersonalityTrait.AGGRESSIVE, 0.05 * intensity)
                self.profile.modify_trait(PersonalityTrait.BRAVE, 0.1 * intensity)
                self.profile.modify_trait(PersonalityTrait.CAUTIOUS, -0.05 * intensity)
            
            elif event == "lost_fight":
                self.profile.modify_trait(PersonalityTrait.AGGRESSIVE, -0.05 * intensity)
                self.profile.modify_trait(PersonalityTrait.BRAVE, -0.1 * intensity)
                self.profile.modify_trait(PersonalityTrait.CAUTIOUS, 0.1 * intensity)
            
            elif event == "made_friend":
                self.profile.modify_trait(PersonalityTrait.SOCIABLE, 0.1 * intensity)
                self.profile.modify_trait(PersonalityTrait.LOYAL, 0.05 * intensity)
            
            elif event == "betrayed":
                self.profile.modify_trait(PersonalityTrait.LOYAL, -0.1 * intensity)
                self.profile.modify_trait(PersonalityTrait.AGGRESSIVE, 0.05 * intensity)
            
            elif event == "discovered_resource":
                self.profile.modify_trait(PersonalityTrait.CURIOUS, 0.1 * intensity)
                self.profile.modify_trait(PersonalityTrait.INTELLIGENT, 0.05 * intensity)
            
            elif event == "built_structure":
                self.profile.modify_trait(PersonalityTrait.CREATIVE, 0.1 * intensity)
                self.profile.modify_trait(PersonalityTrait.AMBITIOUS, 0.05 * intensity)
        
        # Assurer la cohérence après modification
        self._ensure_consistency()
    
    def get_mood(self) -> Tuple[str, float]:
        """
        Obtenir l'humeur actuelle basée sur la personnalité.
        Retourne (nom_humeur, valeur).
        """
        # Calculer une humeur basée sur les traits
        energy = (self.get_trait(PersonalityTrait.AGGRESSIVE) + 
                  self.get_trait(PersonalityTrait.BRAVE)) / 2
        
        sociability = (self.get_trait(PersonalityTrait.SOCIABLE) + 
                       self.get_trait(PersonalityTrait.LOYAL)) / 2
        
        if energy > 0.7 and sociability > 0.7:
            return ("enthousiaste", energy * sociability)
        elif energy > 0.7:
            return ("dynamique", energy)
        elif sociability > 0.7:
            return ("amical", sociability)
        elif energy < 0.3 and sociability < 0.3:
            return ("solitaire", 1 - energy - sociability)
        elif energy < 0.3:
            return ("calme", 1 - energy)
        elif sociability < 0.3:
            return ("indépendant", 1 - sociability)
        else:
            return ("neutre", 0.5)
