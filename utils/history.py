"""
Classe HistoryManager - Gestion de l'historique de la simulation
"""

import time
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque
import threading

from ..config import config, SAVE_DIR
from .logger import Logger


@dataclass
class HistoryEntry:
    """Entrée dans l'historique"""
    timestamp: float
    simulation_time: float
    event_type: str
    entity_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            "timestamp": self.timestamp,
            "simulation_time": self.simulation_time,
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """Créer à partir d'un dictionnaire"""
        return cls(
            timestamp=data.get("timestamp", 0),
            simulation_time=data.get("simulation_time", 0),
            event_type=data.get("event_type", ""),
            entity_id=data.get("entity_id"),
            data=data.get("data", {})
        )


@dataclass
class Snapshot:
    """Instantané de l'état de la simulation"""
    timestamp: float
    simulation_time: float
    agents: List[Dict[str, Any]] = field(default_factory=list)
    structures: List[Dict[str, Any]] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    groups: List[Dict[str, Any]] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            "timestamp": self.timestamp,
            "simulation_time": self.simulation_time,
            "agents": self.agents,
            "structures": self.structures,
            "resources": self.resources,
            "groups": self.groups,
            "stats": self.stats
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        """Créer à partir d'un dictionnaire"""
        return cls(
            timestamp=data.get("timestamp", 0),
            simulation_time=data.get("simulation_time", 0),
            agents=data.get("agents", []),
            structures=data.get("structures", []),
            resources=data.get("resources", []),
            groups=data.get("groups", []),
            stats=data.get("stats", {})
        )


class HistoryManager:
    """
    Gère l'historique de la simulation.
    Enregistre les événements, les instantanés et permet de revenir en arrière.
    """
    
    def __init__(self, max_entries: int = None, max_snapshots: int = None):
        """Initialiser le gestionnaire d'historique"""
        self.max_entries = max_entries or config.simulation.max_history
        self.max_snapshots = max_snapshots or 100
        
        # Historique des événements
        self.entries: deque = deque(maxlen=self.max_entries)
        
        # Instantanés
        self.snapshots: deque = deque(maxlen=self.max_snapshots)
        
        # Index pour la recherche rapide
        self.entity_index: Dict[str, List[int]] = {}  # entity_id -> indices dans entries
        self.event_type_index: Dict[str, List[int]] = {}  # event_type -> indices
        
        # Verrou pour la thread-safety
        self.lock = threading.Lock()
        
        # Logger
        self.logger = Logger("HistoryManager")
        
        # Temps de la dernière sauvegarde
        self.last_save_time = time.time()
        self.auto_save_interval = config.simulation.auto_save_interval
    
    def add_entry(self, event_type: str, entity_id: str = None, 
                  data: Dict[str, Any] = None, simulation_time: float = 0):
        """Ajouter une entrée dans l'historique"""
        if data is None:
            data = {}
        
        entry = HistoryEntry(
            timestamp=time.time(),
            simulation_time=simulation_time,
            event_type=event_type,
            entity_id=entity_id,
            data=data
        )
        
        with self.lock:
            # Ajouter l'entrée
            self.entries.append(entry)
            
            # Mettre à jour les index
            entry_index = len(self.entries) - 1
            
            if entity_id:
                if entity_id not in self.entity_index:
                    self.entity_index[entity_id] = []
                self.entity_index[entity_id].append(entry_index)
            
            if event_type not in self.event_type_index:
                self.event_type_index[event_type] = []
            self.event_type_index[event_type].append(entry_index)
        
        # Vérifier si on doit sauvegarder
        if time.time() - self.last_save_time > self.auto_save_interval:
            self.save_to_file()
            self.last_save_time = time.time()
    
    def add_snapshot(self, agents: List[Dict], structures: List[Dict],
                     resources: List[Dict], groups: List[Dict],
                     stats: Dict, simulation_time: float):
        """Ajouter un instantané de l'état de la simulation"""
        snapshot = Snapshot(
            timestamp=time.time(),
            simulation_time=simulation_time,
            agents=agents,
            structures=structures,
            resources=resources,
            groups=groups,
            stats=stats
        )
        
        with self.lock:
            self.snapshots.append(snapshot)
        
        self.logger.debug(f"Instantané ajouté à t={simulation_time}")
    
    def get_entries(self, limit: int = None, offset: int = 0, 
                    event_type: str = None, entity_id: str = None) -> List[HistoryEntry]:
        """Obtenir des entrées de l'historique"""
        with self.lock:
            entries = list(self.entries)
        
        # Filtrer
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        
        if entity_id:
            entries = [e for e in entries if e.entity_id == entity_id]
        
        # Limiter
        if limit:
            entries = entries[offset:offset + limit]
        else:
            entries = entries[offset:]
        
        return entries
    
    def get_entries_by_entity(self, entity_id: str, limit: int = None) -> List[HistoryEntry]:
        """Obtenir les entrées pour une entité spécifique"""
        with self.lock:
            if entity_id not in self.entity_index:
                return []
            
            indices = self.entity_index[entity_id]
            entries = [self.entries[i] for i in indices if i < len(self.entries)]
            
            if limit:
                return entries[-limit:]
            return entries
    
    def get_entries_by_type(self, event_type: str, limit: int = None) -> List[HistoryEntry]:
        """Obtenir les entrées par type d'événement"""
        with self.lock:
            if event_type not in self.event_type_index:
                return []
            
            indices = self.event_type_index[event_type]
            entries = [self.entries[i] for i in indices if i < len(self.entries)]
            
            if limit:
                return entries[-limit:]
            return entries
    
    def get_latest_snapshot(self) -> Optional[Snapshot]:
        """Obtenir le dernier instantané"""
        with self.lock:
            if self.snapshots:
                return self.snapshots[-1]
            return None
    
    def get_snapshot_at_time(self, simulation_time: float) -> Optional[Snapshot]:
        """Obtenir l'instantané le plus proche d'un temps de simulation"""
        with self.lock:
            # Recherche binaire pour trouver l'instantané le plus proche
            low, high = 0, len(self.snapshots) - 1
            best = None
            best_diff = float('inf')
            
            while low <= high:
                mid = (low + high) // 2
                snapshot = self.snapshots[mid]
                diff = abs(snapshot.simulation_time - simulation_time)
                
                if diff < best_diff:
                    best_diff = diff
                    best = snapshot
                
                if snapshot.simulation_time < simulation_time:
                    low = mid + 1
                else:
                    high = mid - 1
            
            return best
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques de l'historique"""
        with self.lock:
            return {
                "total_entries": len(self.entries),
                "total_snapshots": len(self.snapshots),
                "unique_entities": len(self.entity_index),
                "unique_event_types": len(self.event_type_index)
            }
    
    def clear(self):
        """Effacer l'historique"""
        with self.lock:
            self.entries.clear()
            self.snapshots.clear()
            self.entity_index.clear()
            self.event_type_index.clear()
    
    def save_to_file(self, filename: str = None):
        """Sauvegarder l'historique dans un fichier"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(SAVE_DIR, f"history_{timestamp}.json")
        
        with self.lock:
            data = {
                "entries": [e.to_dict() for e in self.entries],
                "snapshots": [s.to_dict() for s in self.snapshots],
                "stats": self.get_stats()
            }
        
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Historique sauvegardé dans {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def load_from_file(self, filename: str) -> bool:
        """Charger l'historique depuis un fichier"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with self.lock:
                self.entries = deque([
                    HistoryEntry.from_dict(e) for e in data.get("entries", [])
                ], maxlen=self.max_entries)
                
                self.snapshots = deque([
                    Snapshot.from_dict(s) for s in data.get("snapshots", [])
                ], maxlen=self.max_snapshots)
                
                # Reconstruire les index
                self._rebuild_indexes()
            
            self.logger.info(f"Historique chargé depuis {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement: {e}")
            return False
    
    def _rebuild_indexes(self):
        """Reconstruire les index après un chargement"""
        self.entity_index.clear()
        self.event_type_index.clear()
        
        for i, entry in enumerate(self.entries):
            if entry.entity_id:
                if entry.entity_id not in self.entity_index:
                    self.entity_index[entry.entity_id] = []
                self.entity_index[entry.entity_id].append(i)
            
            if entry.event_type not in self.event_type_index:
                self.event_type_index[entry.event_type] = []
            self.event_type_index[entry.event_type].append(i)
    
    def get_timeline(self, entity_id: str = None) -> List[Dict[str, Any]]:
        """Obtenir une timeline des événements"""
        entries = self.get_entries()
        
        if entity_id:
            entries = [e for e in entries if e.entity_id == entity_id]
        
        # Grouper par temps de simulation
        timeline = []
        for entry in entries:
            timeline.append({
                "time": entry.simulation_time,
                "type": entry.event_type,
                "entity": entry.entity_id,
                "data": entry.data
            })
        
        return timeline


# Instance globale du gestionnaire d'historique
history_manager = HistoryManager()
