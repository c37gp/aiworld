"""
Classe EventBus - Système d'événements pour AI World
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum, auto
import threading
import weakref


class EventType(Enum):
    """Types d'événements"""
    # Événements de simulation
    SIMULATION_STARTED = auto()
    SIMULATION_PAUSED = auto()
    SIMULATION_RESUMED = auto()
    SIMULATION_STOPPED = auto()
    TIME_SCALE_CHANGED = auto()
    
    # Événements d'agents
    AGENT_CREATED = auto()
    AGENT_DESTROYED = auto()
    AGENT_MOVED = auto()
    AGENT_SPEAKING = auto()
    AGENT_ATTACKED = auto()
    AGENT_DIED = auto()
    AGENT_BORN = auto()
    
    # Événements sociaux
    GROUP_FORMED = auto()
    GROUP_DISBANDED = auto()
    LEADER_ELECTED = auto()
    RULE_CREATED = auto()
    TRADE_OCCURRED = auto()
    
    # Événements de construction
    STRUCTURE_BUILT = auto()
    STRUCTURE_DESTROYED = auto()
    RESOURCE_HARVESTED = auto()
    
    # Événements de combat
    COMBAT_STARTED = auto()
    COMBAT_ENDED = auto()
    
    # Événements personnalisés
    CUSTOM_EVENT = auto()


@dataclass
class Event:
    """Représente un événement dans le système"""
    event_type: EventType
    sender: Optional[Any] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())
    
    def __post_init__(self):
        import time
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = time.time()


class EventBus:
    """
    Système d'événements pour la communication entre composants.
    Permet l'envoi et la réception d'événements de manière découplée.
    """
    
    def __init__(self):
        """Initialiser le bus d'événements"""
        self.listeners: Dict[EventType, List[Callable[[Event], None]]] = {}
        self.weak_listeners: Dict[EventType, List[weakref.ReferenceType]] = {}
        self.queue: List[Event] = []
        self.lock = threading.Lock()
        self.processing = False
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """S'abonner à un type d'événement"""
        with self.lock:
            if event_type not in self.listeners:
                self.listeners[event_type] = []
            self.listeners[event_type].append(callback)
    
    def subscribe_weak(self, event_type: EventType, callback: Callable[[Event], None]):
        """S'abonner avec une référence faible (pour éviter les fuites mémoire)"""
        with self.lock:
            if event_type not in self.weak_listeners:
                self.weak_listeners[event_type] = []
            self.weak_listeners[event_type].append(weakref.ref(callback))
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Se désabonner d'un type d'événement"""
        with self.lock:
            if event_type in self.listeners:
                if callback in self.listeners[event_type]:
                    self.listeners[event_type].remove(callback)
    
    def emit(self, event: Event):
        """Émettre un événement"""
        with self.lock:
            self.queue.append(event)
            
            # Traiter immédiatement si on n'est pas déjà en train de traiter
            if not self.processing:
                self._process_queue()
    
    def emit_now(self, event: Event):
        """Émettre un événement et le traiter immédiatement"""
        with self.lock:
            self.queue.insert(0, event)  # Ajouter au début pour traitement immédiat
            self._process_queue()
    
    def _process_queue(self):
        """Traiter la file d'attente des événements"""
        self.processing = True
        
        try:
            while self.queue:
                event = self.queue.pop(0)
                self._dispatch_event(event)
        finally:
            self.processing = False
    
    def _dispatch_event(self, event: Event):
        """Dispatcher un événement vers tous les listeners"""
        # Notifier les listeners normaux
        if event.event_type in self.listeners:
            for callback in self.listeners[event.event_type][:]:  # Copie pour éviter les problèmes de modification
                try:
                    callback(event)
                except Exception as e:
                    print(f"Erreur dans le callback pour {event.event_type}: {e}")
        
        # Notifier les listeners faibles
        if event.event_type in self.weak_listeners:
            to_remove = []
            for i, ref in enumerate(self.weak_listeners[event.event_type]):
                callback = ref()
                if callback is None:
                    to_remove.append(i)
                else:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"Erreur dans le callback faible pour {event.event_type}: {e}")
            
            # Supprimer les références faibles qui n'existent plus
            for i in reversed(to_remove):
                del self.weak_listeners[event.event_type][i]
    
    def clear(self):
        """Vider la file d'attente"""
        with self.lock:
            self.queue.clear()
    
    def clear_subscriptions(self):
        """Supprimer tous les abonnements"""
        with self.lock:
            self.listeners.clear()
            self.weak_listeners.clear()
    
    def has_listeners(self, event_type: EventType) -> bool:
        """Vérifier s'il y a des listeners pour un type d'événement"""
        with self.lock:
            return (event_type in self.listeners and len(self.listeners[event_type]) > 0) or \
                   (event_type in self.weak_listeners and len(self.weak_listeners[event_type]) > 0)


# Instance globale du bus d'événements
event_bus = EventBus()
