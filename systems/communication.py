"""
Classe CommunicationSystem - Système de communication entre agents
"""

import time
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque

from ..config import config
from ..utils.vector import Vector2
from ..utils.logger import Logger
from ..agents.ai_agent import AIAgent


class MessageType(Enum):
    """Types de messages"""
    TEXT = auto()          # Message texte
    REQUEST = auto()        # Requête
    OFFER = auto()         # Offre
    WARNING = auto()       # Avertissement
    COMMAND = auto()       # Commande
    QUESTION = auto()      # Question
    ANSWER = auto()        # Réponse
    GOSSIP = auto()        # Commérage
    THREAT = auto()        # Menace
    APPEAL = auto()        # Appel à l'aide


class MessagePriority(Enum):
    """Priorités des messages"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """Représente un message entre agents"""
    sender_id: str
    receiver_id: Optional[str] = None  # None = broadcast
    content: Any = None
    message_type: MessageType = MessageType.TEXT
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    ttl: float = 10.0  # Time to live (secondes)
    
    # Position du sender au moment de l'envoi
    sender_position: Optional[Vector2] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self, current_time: float) -> bool:
        """Vérifier si le message a expiré"""
        return (current_time - self.timestamp) > self.ttl
    
    def get_age(self, current_time: float) -> float:
        """Obtenir l'âge du message"""
        return current_time - self.timestamp


class CommunicationSystem:
    """
    Système de communication entre agents.
    Gère l'envoi, la réception et la propagation des messages.
    """
    
    def __init__(self):
        """Initialiser le système de communication"""
        self.logger = Logger("CommunicationSystem")
        
        # Messages en attente
        self.message_queue: deque = deque()
        
        # Messages reçus par agent
        self.inboxes: Dict[str, deque] = {}
        
        # Messages envoyés par agent (pour l'historique)
        self.outboxes: Dict[str, deque] = {}
        
        # Abonnements aux types de messages
        self.subscriptions: Dict[str, Set[MessageType]] = {}
        
        # Callbacks pour les messages
        self.message_callbacks: Dict[str, List[Callable[[Message], None]]] = {}
        
        # Historique des messages
        self.message_history: List[Message] = []
        self.max_history = 1000
        
        # Statistiques
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_expired": 0,
            "broadcasts": 0
        }
    
    def register_agent(self, agent_id: str):
        """Enregistrer un nouvel agent"""
        if agent_id not in self.inboxes:
            self.inboxes[agent_id] = deque(maxlen=100)
        if agent_id not in self.outboxes:
            self.outboxes[agent_id] = deque(maxlen=100)
        if agent_id not in self.subscriptions:
            self.subscriptions[agent_id] = set()
        if agent_id not in self.message_callbacks:
            self.message_callbacks[agent_id] = []
    
    def unregister_agent(self, agent_id: str):
        """Désenregistrer un agent"""
        if agent_id in self.inboxes:
            del self.inboxes[agent_id]
        if agent_id in self.outboxes:
            del self.outboxes[agent_id]
        if agent_id in self.subscriptions:
            del self.subscriptions[agent_id]
        if agent_id in self.message_callbacks:
            del self.message_callbacks[agent_id]
    
    def send_message(self, sender: AIAgent, receiver_id: Optional[str] = None,
                     content: Any = None, message_type: MessageType = MessageType.TEXT,
                     priority: MessagePriority = MessagePriority.NORMAL,
                     ttl: float = None, metadata: Dict[str, Any] = None) -> Message:
        """Envoyer un message"""
        if metadata is None:
            metadata = {}
        
        message = Message(
            sender_id=sender.agent_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
            priority=priority,
            ttl=ttl or config.agent.communication_range / sender.speed,
            sender_position=sender.position.copy(),
            metadata=metadata
        )
        
        # Ajouter à la file d'attente
        self.message_queue.append(message)
        
        # Ajouter à l'outbox du sender
        if sender.agent_id in self.outboxes:
            self.outboxes[sender.agent_id].append(message)
        
        # Statistiques
        self.stats["messages_sent"] += 1
        if receiver_id is None:
            self.stats["broadcasts"] += 1
        
        self.logger.debug(f"Message envoyé: {sender.name} -> {receiver_id or 'ALL'} ({message_type.name})")
        
        return message
    
    def broadcast(self, sender: AIAgent, content: Any, message_type: MessageType = MessageType.TEXT,
                  priority: MessagePriority = MessagePriority.NORMAL,
                  range_limit: float = None) -> Message:
        """Envoyer un message à tous les agents à proximité"""
        message = self.send_message(
            sender=sender,
            receiver_id=None,  # Broadcast
            content=content,
            message_type=message_type,
            priority=priority,
            ttl=range_limit / sender.speed if range_limit else None
        )
        return message
    
    def send_to_group(self, sender: AIAgent, group_id: str, content: Any,
                      message_type: MessageType = MessageType.TEXT,
                      priority: MessagePriority = MessagePriority.NORMAL) -> Message:
        """Envoyer un message à tous les membres d'un groupe"""
        # Pour l'instant, envoyer un broadcast (à améliorer)
        return self.broadcast(sender, content, message_type, priority)
    
    def receive_messages(self, agent_id: str) -> List[Message]:
        """Recevoir les messages pour un agent"""
        if agent_id not in self.inboxes:
            return []
        
        messages = []
        current_time = time.time()
        
        # Traiter la file d'attente
        while self.message_queue:
            message = self.message_queue[0]
            
            # Vérifier si le message a expiré
            if message.is_expired(current_time):
                self.message_queue.popleft()
                self.stats["messages_expired"] += 1
                continue
            
            # Vérifier si le message est pour cet agent ou un broadcast
            if message.receiver_id is None or message.receiver_id == agent_id:
                # Vérifier la portée (si le message a une position)
                if message.sender_position:
                    # Dans une implémentation complète, on vérifierait la distance
                    # entre l'agent et le sender_position
                    pass
                
                # Ajouter à l'inbox
                self.inboxes[agent_id].append(message)
                self.message_queue.popleft()
                
                # Statistiques
                self.stats["messages_received"] += 1
            else:
                break  # Les messages sont triés, on peut arrêter
        
        # Récupérer les messages de l'inbox
        while self.inboxes[agent_id]:
            messages.append(self.inboxes[agent_id].popleft())
        
        return messages
    
    def process_messages(self, agent: AIAgent):
        """Traiter les messages pour un agent"""
        messages = self.receive_messages(agent.agent_id)
        
        for message in messages:
            # Mémoriser le message
            agent.memory.add_memory(
                content=message.content,
                memory_type=MemoryType.SHORT_TERM,
                tags=["message", message.message_type.name.lower()]
            )
            
            # Appeler les callbacks
            if agent.agent_id in self.message_callbacks:
                for callback in self.message_callbacks[agent.agent_id]:
                    callback(message)
            
            # Traiter le message en fonction du type
            self._process_message_type(agent, message)
    
    def _process_message_type(self, agent: AIAgent, message: Message):
        """Traiter un message en fonction de son type"""
        if message.message_type == MessageType.REQUEST:
            self._handle_request(agent, message)
        
        elif message.message_type == MessageType.OFFER:
            self._handle_offer(agent, message)
        
        elif message.message_type == MessageType.WARNING:
            self._handle_warning(agent, message)
        
        elif message.message_type == MessageType.COMMAND:
            self._handle_command(agent, message)
        
        elif message.message_type == MessageType.QUESTION:
            self._handle_question(agent, message)
        
        elif message.message_type == MessageType.THREAT:
            self._handle_threat(agent, message)
        
        elif message.message_type == MessageType.APPEAL:
            self._handle_appeal(agent, message)
    
    def _handle_request(self, agent: AIAgent, message: Message):
        """Traiter une requête"""
        # Répondre en fonction de la personnalité
        compatibility = agent.personality.get_trait(PersonalityTrait.LOYAL)
        
        if compatibility > 0.7:
            # Accepter la requête
            response = f"OK: {message.content}"
            self.send_message(
                agent,
                message.sender_id,
                response,
                MessageType.ANSWER
            )
        else:
            # Refuser
            response = f"REFUSED: {message.content}"
            self.send_message(
                agent,
                message.sender_id,
                response,
                MessageType.ANSWER
            )
    
    def _handle_offer(self, agent: AIAgent, message: Message):
        """Traiter une offre"""
        # Mémoriser l'offre
        agent.memory.add_memory(
            content=f"Offre reçue: {message.content}",
            memory_type=MemoryType.SHORT_TERM,
            tags=["offer", "trade"]
        )
    
    def _handle_warning(self, agent: AIAgent, message: Message):
        """Traiter un avertissement"""
        # Réagir en fonction de la personnalité
        if agent.personality.get_trait(PersonalityTrait.CAUTIOUS) > 0.5:
            # Prendre des précautions
            agent.communicate(f"Merci pour l'avertissement!", message.sender_id)
        else:
            # Ignorer ou minimiser
            agent.communicate(f"Pas de problème.", message.sender_id)
    
    def _handle_command(self, agent: AIAgent, message: Message):
        """Traiter une commande"""
        # Vérifier si l'agent est dans un groupe et si le sender est le leader
        if (agent.group_id and 
            message.sender_id in agent.memory.social and
            agent.memory.social[message.sender_id].relationship == "leader"):
            
            # Exécuter la commande
            agent.communicate(f"Commande reçue: {message.content}", message.sender_id)
        else:
            # Ignorer ou refuser
            agent.communicate(f"Je ne prends pas d'ordres de toi.", message.sender_id)
    
    def _handle_question(self, agent: AIAgent, message: Message):
        """Traiter une question"""
        # Répondre en fonction de la connaissance
        if message.content in agent.memory.semantic:
            knowledge = agent.memory.semantic[message.content]
            response = f"Réponse: {knowledge.content}"
        else:
            response = f"Je ne sais pas."
        
        self.send_message(
            agent,
            message.sender_id,
            response,
            MessageType.ANSWER
        )
    
    def _handle_threat(self, agent: AIAgent, message: Message):
        """Traiter une menace"""
        # Réagir en fonction de la personnalité
        if agent.personality.get_trait(PersonalityTrait.AGGRESSIVE) > 0.7:
            # Contrer la menace
            agent.communicate(f"Essaie donc!", message.sender_id)
        else:
            # Se soumettre ou fuir
            agent.communicate(f"Je ne veux pas de problèmes.", message.sender_id)
    
    def _handle_appeal(self, agent: AIAgent, message: Message):
        """Traiter un appel à l'aide"""
        # Réagir en fonction de la personnalité
        if agent.personality.get_trait(PersonalityTrait.LOYAL) > 0.7:
            # Aider
            agent.communicate(f"J'arrive!", message.sender_id)
        else:
            # Ignorer
            pass
    
    def subscribe(self, agent_id: str, message_type: MessageType):
        """S'abonner à un type de message"""
        if agent_id in self.subscriptions:
            self.subscriptions[agent_id].add(message_type)
    
    def unsubscribe(self, agent_id: str, message_type: MessageType):
        """Se désabonner d'un type de message"""
        if agent_id in self.subscriptions:
            self.subscriptions[agent_id].discard(message_type)
    
    def add_callback(self, agent_id: str, callback: Callable[[Message], None]):
        """Ajouter un callback pour les messages"""
        if agent_id in self.message_callbacks:
            self.message_callbacks[agent_id].append(callback)
    
    def remove_callback(self, agent_id: str, callback: Callable[[Message], None]):
        """Supprimer un callback"""
        if agent_id in self.message_callbacks:
            if callback in self.message_callbacks[agent_id]:
                self.message_callbacks[agent_id].remove(callback)
    
    def get_message_history(self, agent_id: str, limit: int = 100) -> List[Message]:
        """Obtenir l'historique des messages pour un agent"""
        history = []
        
        if agent_id in self.outboxes:
            history.extend(self.outboxes[agent_id])
        
        if agent_id in self.inboxes:
            history.extend(self.inboxes[agent_id])
        
        # Trier par timestamp
        history.sort(key=lambda m: m.timestamp, reverse=True)
        
        return history[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du système"""
        return {
            **self.stats,
            "queue_size": len(self.message_queue),
            "inboxes": {k: len(v) for k, v in self.inboxes.items()},
            "outboxes": {k: len(v) for k, v in self.outboxes.items()}
        }
    
    def clear(self):
        """Effacer tous les messages"""
        self.message_queue.clear()
        for inbox in self.inboxes.values():
            inbox.clear()
        for outbox in self.outboxes.values():
            outbox.clear()
        self.message_history.clear()
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_expired": 0,
            "broadcasts": 0
        }
