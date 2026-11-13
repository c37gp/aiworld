"""
Classe AgentMemory - Système de mémoire pour les agents IA
"""

import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque

from ..config import config
from ..utils.vector import Vector2
from ..utils.logger import Logger


class MemoryType(Enum):
    """Types de mémoire"""
    SHORT_TERM = auto()    # Mémoire à court terme (récent)
    LONG_TERM = auto()     # Mémoire à long terme (important)
    EPISODIC = auto()      # Mémoire épisodique (événements)
    SEMANTIC = auto()     # Mémoire sémantique (connaissances)
    SPATIAL = auto()       # Mémoire spatiale (positions)
    SOCIAL = auto()        # Mémoire sociale (relations)


@dataclass
class MemoryEntry:
    """Entrée de mémoire"""
    content: Any
    memory_type: MemoryType
    timestamp: float
    strength: float = 1.0  # Force de la mémoire (0-1)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = time.time()
    
    def decay(self, delta_time: float, decay_rate: float = 0.001):
        """Faire décroître la force de la mémoire"""
        self.strength = max(0, self.strength - delta_time * decay_rate)
    
    def reinforce(self, amount: float = 0.1):
        """Renforcer la mémoire"""
        self.strength = min(1.0, self.strength + amount)


@dataclass
class SpatialMemory:
    """Mémoire spatiale pour les positions"""
    position: Vector2
    entity_type: str  # "resource", "agent", "structure", etc.
    entity_id: Optional[str] = None
    last_seen: float = field(default_factory=time.time)
    visits: int = 0
    
    def update(self, position: Vector2 = None):
        """Mettre à jour la mémoire spatiale"""
        if position:
            self.position = position
        self.last_seen = time.time()
        self.visits += 1


@dataclass
class SocialMemory:
    """Mémoire sociale pour les relations"""
    agent_id: str
    name: str
    relationship: str  # "friend", "enemy", "neutral", "leader", "follower", etc.
    trust: float = 0.5  # Niveau de confiance (0-1)
    last_interaction: float = field(default_factory=time.time)
    interaction_count: int = 0
    
    def update_trust(self, delta: float):
        """Mettre à jour la confiance"""
        self.trust = max(0, min(1, self.trust + delta))
    
    def record_interaction(self, interaction_type: str):
        """Enregistrer une interaction"""
        self.last_interaction = time.time()
        self.interaction_count += 1
        
        # Mettre à jour la confiance en fonction du type d'interaction
        trust_changes = {
            "trade_success": 0.1,
            "trade_fail": -0.1,
            "help": 0.2,
            "attack": -0.3,
            "defend": 0.15,
            "share_knowledge": 0.1,
            "lie": -0.2
        }
        
        if interaction_type in trust_changes:
            self.update_trust(trust_changes[interaction_type])


@dataclass
class KnowledgeEntry:
    """Entrée de connaissance"""
    topic: str
    content: Any
    source: str  # ID de l'agent source
    learned_at: float = field(default_factory=time.time)
    confidence: float = 0.5  # Niveau de confiance dans la connaissance (0-1)
    
    def update_confidence(self, delta: float):
        """Mettre à jour la confiance"""
        self.confidence = max(0, min(1, self.confidence + delta))


class AgentMemory:
    """
    Système de mémoire pour un agent IA.
    Permet de stocker, récupérer et oublier des informations.
    """
    
    def __init__(self, agent_id: str, capacity: int = None):
        """Initialiser la mémoire"""
        self.agent_id = agent_id
        self.capacity = capacity or config.agent.memory_capacity
        
        # Différents types de mémoire
        self.short_term: deque = deque(maxlen=100)  # Mémoire à court terme
        self.long_term: List[MemoryEntry] = []  # Mémoire à long terme
        self.episodic: List[MemoryEntry] = []  # Mémoire épisodique
        self.semantic: Dict[str, KnowledgeEntry] = {}  # Mémoire sémantique
        
        # Mémoire spatiale
        self.spatial: Dict[str, SpatialMemory] = {}  # entity_id -> SpatialMemory
        
        # Mémoire sociale
        self.social: Dict[str, SocialMemory] = {}  # agent_id -> SocialMemory
        
        # Statistiques
        self.stats = {
            "total_memories": 0,
            "forgotten_memories": 0,
            "knowledge_shared": 0,
            "knowledge_received": 0
        }
        
        # Logger
        self.logger = Logger(f"Memory_{agent_id}")
    
    def add_memory(self, content: Any, memory_type: MemoryType, 
                   tags: List[str] = None, strength: float = 1.0) -> MemoryEntry:
        """Ajouter une mémoire"""
        if tags is None:
            tags = []
        
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            strength=strength,
            tags=tags
        )
        
        # Ajouter à la mémoire appropriée
        if memory_type == MemoryType.SHORT_TERM:
            self.short_term.append(entry)
        elif memory_type == MemoryType.LONG_TERM:
            self.long_term.append(entry)
        elif memory_type == MemoryType.EPISODIC:
            self.episodic.append(entry)
        
        self.stats["total_memories"] += 1
        
        # Vérifier la capacité
        self._check_capacity()
        
        return entry
    
    def add_knowledge(self, topic: str, content: Any, source: str, 
                      confidence: float = 0.5) -> KnowledgeEntry:
        """Ajouter une connaissance"""
        entry = KnowledgeEntry(
            topic=topic,
            content=content,
            source=source,
            confidence=confidence
        )
        
        self.semantic[topic] = entry
        self.stats["total_memories"] += 1
        self.stats["knowledge_received"] += 1
        
        return entry
    
    def add_spatial_memory(self, entity_id: str, entity_type: str, 
                           position: Vector2, name: str = None) -> SpatialMemory:
        """Ajouter une mémoire spatiale"""
        memory = SpatialMemory(
            position=position,
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        self.spatial[entity_id] = memory
        return memory
    
    def add_social_memory(self, agent_id: str, name: str, 
                          relationship: str = "neutral") -> SocialMemory:
        """Ajouter une mémoire sociale"""
        memory = SocialMemory(
            agent_id=agent_id,
            name=name,
            relationship=relationship
        )
        
        self.social[agent_id] = memory
        return memory
    
    def get_memory(self, memory_type: MemoryType, index: int = None) -> Optional[MemoryEntry]:
        """Obtenir une mémoire"""
        if memory_type == MemoryType.SHORT_TERM:
            if index is None or index < 0:
                return self.short_term[-1] if self.short_term else None
            return self.short_term[index] if index < len(self.short_term) else None
        
        elif memory_type == MemoryType.LONG_TERM:
            if index is None or index < 0:
                return self.long_term[-1] if self.long_term else None
            return self.long_term[index] if index < len(self.long_term) else None
        
        elif memory_type == MemoryType.EPISODIC:
            if index is None or index < 0:
                return self.episodic[-1] if self.episodic else None
            return self.episodic[index] if index < len(self.episodic) else None
        
        return None
    
    def get_knowledge(self, topic: str) -> Optional[KnowledgeEntry]:
        """Obtenir une connaissance"""
        return self.semantic.get(topic)
    
    def get_spatial_memory(self, entity_id: str) -> Optional[SpatialMemory]:
        """Obtenir une mémoire spatiale"""
        return self.spatial.get(entity_id)
    
    def get_social_memory(self, agent_id: str) -> Optional[SocialMemory]:
        """Obtenir une mémoire sociale"""
        return self.social.get(agent_id)
    
    def get_memories_by_tag(self, tag: str) -> List[MemoryEntry]:
        """Obtenir les mémoires avec un tag spécifique"""
        memories = []
        
        for memory in self.short_term:
            if tag in memory.tags:
                memories.append(memory)
        
        for memory in self.long_term:
            if tag in memory.tags:
                memories.append(memory)
        
        for memory in self.episodic:
            if tag in memory.tags:
                memories.append(memory)
        
        return memories
    
    def get_all_knowledge(self) -> List[KnowledgeEntry]:
        """Obtenir toute la connaissance"""
        return list(self.semantic.values())
    
    def get_all_social_memories(self) -> List[SocialMemory]:
        """Obtenir toutes les mémoires sociales"""
        return list(self.social.values())
    
    def get_friends(self) -> List[SocialMemory]:
        """Obtenir les amis"""
        return [m for m in self.social.values() if m.relationship == "friend"]
    
    def get_enemies(self) -> List[SocialMemory]:
        """Obtenir les ennemis"""
        return [m for m in self.social.values() if m.relationship == "enemy"]
    
    def get_leader(self) -> Optional[SocialMemory]:
        """Obtenir le leader"""
        for memory in self.social.values():
            if memory.relationship == "leader":
                return memory
        return None
    
    def forget_memory(self, memory_type: MemoryType, index: int) -> bool:
        """Oublier une mémoire"""
        if memory_type == MemoryType.SHORT_TERM and 0 <= index < len(self.short_term):
            del self.short_term[index]
            self.stats["forgotten_memories"] += 1
            return True
        
        elif memory_type == MemoryType.LONG_TERM and 0 <= index < len(self.long_term):
            del self.long_term[index]
            self.stats["forgotten_memories"] += 1
            return True
        
        elif memory_type == MemoryType.EPISODIC and 0 <= index < len(self.episodic):
            del self.episodic[index]
            self.stats["forgotten_memories"] += 1
            return True
        
        return False
    
    def forget_knowledge(self, topic: str) -> bool:
        """Oublier une connaissance"""
        if topic in self.semantic:
            del self.semantic[topic]
            self.stats["forgotten_memories"] += 1
            return True
        return False
    
    def update(self, delta_time: float):
        """Mettre à jour la mémoire (décroissance, etc.)"""
        # Faire décroître la mémoire à court terme
        decay_rate = 0.01
        for memory in self.short_term:
            memory.decay(delta_time, decay_rate)
        
        # Supprimer les mémoires à court terme faibles
        while self.short_term and self.short_term[0].strength < 0.1:
            self.short_term.popleft()
            self.stats["forgotten_memories"] += 1
        
        # Faire décroître la mémoire à long terme (plus lentement)
        for memory in self.long_term:
            memory.decay(delta_time, decay_rate * 0.1)
        
        # Supprimer les mémoires à long terme faibles
        self.long_term = [m for m in self.long_term if m.strength >= 0.05]
    
    def _check_capacity(self):
        """Vérifier la capacité de la mémoire"""
        total = (len(self.short_term) + len(self.long_term) + 
                len(self.episodic) + len(self.semantic))
        
        if total > self.capacity:
            # Supprimer les mémoires les plus anciennes
            if self.short_term:
                self.short_term.popleft()
                self.stats["forgotten_memories"] += 1
            
            elif self.long_term:
                self.long_term.pop(0)
                self.stats["forgotten_memories"] += 1
    
    def share_knowledge(self, topic: str, target_memory: "AgentMemory") -> bool:
        """Partager une connaissance avec un autre agent"""
        if topic in self.semantic:
            knowledge = self.semantic[topic]
            
            # Créer une nouvelle entrée pour l'autre agent
            target_memory.add_knowledge(
                topic=topic,
                content=knowledge.content,
                source=self.agent_id,
                confidence=knowledge.confidence * 0.9  # Légère perte de confiance
            )
            
            self.stats["knowledge_shared"] += 1
            return True
        
        return False
    
    def remember_position(self, entity_id: str, position: Vector2, 
                          entity_type: str = "unknown") -> bool:
        """Mémoriser une position"""
        if entity_id in self.spatial:
            self.spatial[entity_id].update(position)
        else:
            self.add_spatial_memory(entity_id, entity_type, position)
        return True
    
    def get_remembered_position(self, entity_id: str) -> Optional[Vector2]:
        """Obtenir une position mémorisée"""
        if entity_id in self.spatial:
            return self.spatial[entity_id].position
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques de la mémoire"""
        return {
            **self.stats,
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "episodic_count": len(self.episodic),
            "semantic_count": len(self.semantic),
            "spatial_count": len(self.spatial),
            "social_count": len(self.social)
        }
    
    def clear(self):
        """Effacer toute la mémoire"""
        self.short_term.clear()
        self.long_term.clear()
        self.episodic.clear()
        self.semantic.clear()
        self.spatial.clear()
        self.social.clear()
        self.stats = {
            "total_memories": 0,
            "forgotten_memories": 0,
            "knowledge_shared": 0,
            "knowledge_received": 0
        }
