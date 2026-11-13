"""
Classe Logger - Système de journalisation pour AI World
"""

import time
import os
from typing import Dict, List, Optional, TextIO
from dataclasses import dataclass, field
from enum import Enum, auto
import threading

from ..config import LOG_DIR


class LogLevel(Enum):
    """Niveaux de journalisation"""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class LogEntry:
    """Entrée de journal"""
    timestamp: float
    level: LogLevel
    module: str
    message: str
    thread_id: int = field(default_factory=lambda: threading.get_ident())
    
    def get_formatted_time(self) -> str:
        """Obtenir l'heure formatée"""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
    
    def get_level_name(self) -> str:
        """Obtenir le nom du niveau"""
        return self.level.name
    
    def format(self) -> str:
        """Formater l'entrée de journal"""
        return f"[{self.get_formatted_time()}] [{self.get_level_name()}] [{self.module}] {self.message}"


class Logger:
    """
    Système de journalisation pour AI World.
    Permet de logger des messages avec différents niveaux de sévérité.
    """
    
    # Instance globale par défaut
    _default_logger: Optional["Logger"] = None
    
    def __init__(self, module: str, level: LogLevel = LogLevel.INFO, 
                 log_file: Optional[str] = None, use_console: bool = True):
        """Initialiser le logger"""
        self.module = module
        self.level = level
        self.log_file = log_file
        self.use_console = use_console
        
        # Fichier de log
        self.file_handle: Optional[TextIO] = None
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            self.file_handle = open(log_file, "a", encoding="utf-8")
        
        # Buffer pour les logs
        self.buffer: List[LogEntry] = []
        self.max_buffer_size = 1000
        
        # Verrou pour la thread-safety
        self.lock = threading.Lock()
    
    def _should_log(self, level: LogLevel) -> bool:
        """Vérifier si on doit logger ce niveau"""
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        return level_order[level] >= level_order[self.level]
    
    def _create_entry(self, level: LogLevel, message: str) -> LogEntry:
        """Créer une entrée de log"""
        return LogEntry(
            timestamp=time.time(),
            level=level,
            module=self.module,
            message=message
        )
    
    def _write_entry(self, entry: LogEntry):
        """Écrire une entrée de log"""
        with self.lock:
            # Ajouter au buffer
            self.buffer.append(entry)
            if len(self.buffer) > self.max_buffer_size:
                self.buffer.pop(0)
            
            # Formater le message
            formatted = entry.format()
            
            # Écrire dans la console
            if self.use_console:
                self._print_to_console(entry.level, formatted)
            
            # Écrire dans le fichier
            if self.file_handle:
                self.file_handle.write(formatted + "\n")
                self.file_handle.flush()
    
    def _print_to_console(self, level: LogLevel, message: str):
        """Afficher dans la console avec la couleur appropriée"""
        colors = {
            LogLevel.DEBUG: "\033[94m",    # Bleu
            LogLevel.INFO: "\033[92m",     # Vert
            LogLevel.WARNING: "\033[93m",  # Jaune
            LogLevel.ERROR: "\033[91m",    # Rouge
            LogLevel.CRITICAL: "\033[95m"  # Magenta
        }
        reset = "\033[0m"
        
        color = colors.get(level, "")
        print(f"{color}{message}{reset}")
    
    def debug(self, message: str):
        """Logger un message de debug"""
        if self._should_log(LogLevel.DEBUG):
            entry = self._create_entry(LogLevel.DEBUG, message)
            self._write_entry(entry)
    
    def info(self, message: str):
        """Logger un message d'information"""
        if self._should_log(LogLevel.INFO):
            entry = self._create_entry(LogLevel.INFO, message)
            self._write_entry(entry)
    
    def warning(self, message: str):
        """Logger un avertissement"""
        if self._should_log(LogLevel.WARNING):
            entry = self._create_entry(LogLevel.WARNING, message)
            self._write_entry(entry)
    
    def error(self, message: str):
        """Logger une erreur"""
        if self._should_log(LogLevel.ERROR):
            entry = self._create_entry(LogLevel.ERROR, message)
            self._write_entry(entry)
    
    def critical(self, message: str):
        """Logger un message critique"""
        if self._should_log(LogLevel.CRITICAL):
            entry = self._create_entry(LogLevel.CRITICAL, message)
            self._write_entry(entry)
    
    def get_buffer(self) -> List[LogEntry]:
        """Obtenir le buffer des logs"""
        with self.lock:
            return self.buffer.copy()
    
    def clear_buffer(self):
        """Vider le buffer"""
        with self.lock:
            self.buffer.clear()
    
    def close(self):
        """Fermer le logger"""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
    
    @classmethod
    def get_default(cls) -> "Logger":
        """Obtenir le logger par défaut"""
        if cls._default_logger is None:
            cls._default_logger = cls("AIWorld", LogLevel.INFO)
        return cls._default_logger
    
    @classmethod
    def set_default(cls, logger: "Logger"):
        """Définir le logger par défaut"""
        cls._default_logger = logger


# Créer un logger global pour le fichier
main_logger = Logger("AIWorld", LogLevel.INFO, 
                     log_file=os.path.join(LOG_DIR, "ai_world.log"))
