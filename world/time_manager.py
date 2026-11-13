"""
Classe TimeManager - Gestion du temps dans la simulation
"""

import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..config import config, SimulationMode


class TimeScale(Enum):
    """Échelles de temps"""
    PAUSED = 0
    SLOW = 0.5
    NORMAL = 1.0
    FAST = 2.0
    VERY_FAST = 5.0
    INSTANT = 10.0


@dataclass
class TimeEvent:
    """Événement temporel"""
    name: str
    start_time: float
    duration: float
    callback: Optional[Callable] = None
    completed: bool = False
    
    def update(self, delta_time: float) -> bool:
        """Mettre à jour l'événement, retourne True si terminé"""
        if self.completed:
            return True
        
        self.duration -= delta_time
        if self.duration <= 0:
            self.completed = True
            if self.callback:
                self.callback()
            return True
        return False


class TimeManager:
    """
    Gère le temps dans la simulation.
    Permet de contrôler la vitesse, de mettre en pause, et de gérer les événements temporels.
    """
    
    def __init__(self):
        """Initialiser le gestionnaire de temps"""
        self.start_time = time.time()
        self.simulation_time = 0.0  # Temps de simulation (en secondes)
        self.real_time = 0.0  # Temps réel écoulé
        self.last_update_time = time.time()
        
        # Mode de simulation
        self.mode = SimulationMode.REAL_TIME
        self.time_scale = TimeScale.NORMAL.value
        
        # Historique des événements
        self.events: Dict[str, TimeEvent] = {}
        self.event_counter = 0
        
        # Callbacks pour les mises à jour
        self.update_callbacks: List[Callable[[float], None]] = []
        
        # Statistiques
        self.total_ticks = 0
        self.tick_duration = 1.0 / config.simulation.tick_rate
    
    def update(self, delta_time: float):
        """Mettre à jour le gestionnaire de temps"""
        self.real_time += delta_time
        
        # Calculer le delta_time de simulation en fonction de l'échelle
        if self.mode == SimulationMode.PAUSED:
            sim_delta = 0.0
        elif self.mode == SimulationMode.STEP_BY_STEP:
            sim_delta = 0.0  # Attend un step manuel
        else:
            sim_delta = delta_time * self.time_scale
        
        self.simulation_time += sim_delta
        
        # Mettre à jour les événements
        completed_events = []
        for event_id, event in self.events.items():
            if event.update(sim_delta):
                completed_events.append(event_id)
        
        # Supprimer les événements terminés
        for event_id in completed_events:
            del self.events[event_id]
        
        # Appeler les callbacks de mise à jour
        for callback in self.update_callbacks:
            callback(sim_delta)
    
    def step(self):
        """Avancer d'un pas (pour le mode step-by-step)"""
        if self.mode == SimulationMode.STEP_BY_STEP:
            sim_delta = self.tick_duration * self.time_scale
            self.simulation_time += sim_delta
            self.total_ticks += 1
            
            # Mettre à jour les événements
            completed_events = []
            for event_id, event in self.events.items():
                if event.update(sim_delta):
                    completed_events.append(event_id)
            
            for event_id in completed_events:
                del self.events[event_id]
            
            # Appeler les callbacks
            for callback in self.update_callbacks:
                callback(sim_delta)
    
    def set_mode(self, mode: SimulationMode):
        """Définir le mode de simulation"""
        self.mode = mode
    
    def set_time_scale(self, scale: float):
        """Définir l'échelle de temps"""
        self.time_scale = max(0, scale)
    
    def get_time_scale(self) -> float:
        """Obtenir l'échelle de temps actuelle"""
        return self.time_scale
    
    def get_mode(self) -> SimulationMode:
        """Obtenir le mode de simulation actuel"""
        return self.mode
    
    def add_event(self, name: str, duration: float, callback: Callable = None) -> str:
        """Ajouter un événement temporel"""
        event_id = f"event_{self.event_counter}"
        self.event_counter += 1
        
        event = TimeEvent(
            name=name,
            start_time=self.simulation_time,
            duration=duration,
            callback=callback
        )
        
        self.events[event_id] = event
        return event_id
    
    def remove_event(self, event_id: str):
        """Supprimer un événement"""
        if event_id in self.events:
            del self.events[event_id]
    
    def get_event(self, event_id: str) -> Optional[TimeEvent]:
        """Obtenir un événement"""
        return self.events.get(event_id)
    
    def add_update_callback(self, callback: Callable[[float], None]):
        """Ajouter un callback de mise à jour"""
        self.update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable[[float], None]):
        """Supprimer un callback de mise à jour"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def get_simulation_time(self) -> float:
        """Obtenir le temps de simulation écoulé (en secondes)"""
        return self.simulation_time
    
    def get_real_time(self) -> float:
        """Obtenir le temps réel écoulé (en secondes)"""
        return self.real_time
    
    def get_ticks(self) -> int:
        """Obtenir le nombre total de ticks"""
        return self.total_ticks
    
    def get_time_string(self) -> str:
        """Obtenir une représentation lisible du temps de simulation"""
        hours = int(self.simulation_time // 3600)
        minutes = int((self.simulation_time % 3600) // 60)
        seconds = int(self.simulation_time % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_date_string(self) -> str:
        """Obtenir une représentation de date (jours, heures, minutes)"""
        total_seconds = self.simulation_time
        days = int(total_seconds // 86400)
        remaining = total_seconds % 86400
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        
        return f"Jour {days}, {hours:02d}:{minutes:02d}"
    
    def reset(self):
        """Réinitialiser le gestionnaire de temps"""
        self.start_time = time.time()
        self.simulation_time = 0.0
        self.real_time = 0.0
        self.last_update_time = time.time()
        self.events.clear()
        self.event_counter = 0
        self.total_ticks = 0
