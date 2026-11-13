"""
Fonctions utilitaires diverses
"""

import random
import uuid
import time
from typing import List, Tuple, Dict, Any, Callable, TypeVar
from functools import wraps

T = TypeVar('T')


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Limiter une valeur entre min et max"""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """Interpolation linéaire"""
    return a + (b - a) * t


def normalize(value: float, min_val: float, max_val: float) -> float:
    """Normaliser une valeur entre 0 et 1"""
    if max_val - min_val == 0:
        return 0.0
    return (value - min_val) / (max_val - min_val)


def random_choice_with_weights(items: List[T], weights: List[float]) -> T:
    """Choisir un élément aléatoire avec des poids"""
    if not items:
        raise ValueError("Items list cannot be empty")
    if len(items) != len(weights):
        raise ValueError("Items and weights must have the same length")
    
    total_weight = sum(weights)
    if total_weight <= 0:
        return random.choice(items)
    
    r = random.uniform(0, total_weight)
    cumulative = 0.0
    
    for item, weight in zip(items, weights):
        cumulative += weight
        if r <= cumulative:
            return item
    
    return items[-1]


def generate_id(prefix: str = "") -> str:
    """Générer un identifiant unique"""
    unique_id = str(uuid.uuid4())[:8]
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id


def generate_name() -> str:
    """Générer un nom aléatoire pour un agent"""
    first_names = [
        "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
        "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
        "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega",
        "Ada", "Alan", "Grace", "John", "Linus", "Richard", "Dennis", "Guido",
        "Larry", "Sergey", "Mark", "Elon", "Jeff", "Bill", "Steve", "Tim"
    ]
    
    last_names = [
        "Turing", "Lovelace", "VonNeumann", "Knuth", "Dijkstra", "Hoare",
        "Ritchie", "Stallman", "Torvalds", "Page", "Brin", "Zuckerberg",
        "Musk", "Bezos", "Gates", "Jobs", "Cook", "Berners-Lee"
    ]
    
    return f"{random.choice(first_names)}_{random.choice(last_names)}"


def generate_color() -> Tuple[int, int, int]:
    """Générer une couleur aléatoire"""
    return (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))


def time_function(func: Callable) -> Callable:
    """Décorateur pour mesurer le temps d'exécution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Décorateur pour réessayer une fonction"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


def format_number(num: float, precision: int = 2) -> str:
    """Formater un nombre avec une précision donnée"""
    return f"{num:.{precision}f}"


def format_time(seconds: float) -> str:
    """Formater un temps en secondes en une chaîne lisible"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


def get_direction_vector(angle_deg: float) -> Tuple[float, float]:
    """Obtenir un vecteur de direction à partir d'un angle en degrés"""
    import math
    angle_rad = math.radians(angle_deg)
    return (math.cos(angle_rad), math.sin(angle_rad))


def distance_squared(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculer le carré de la distance entre deux points"""
    return (x1 - x2) ** 2 + (y1 - y2) ** 2


def point_in_rect(px: float, py: float, rx: float, ry: float, rw: float, rh: float) -> bool:
    """Vérifier si un point est dans un rectangle"""
    return (px >= rx and px <= rx + rw and 
            py >= ry and py <= ry + rh)


def line_intersects_rect(lx1: float, ly1: float, lx2: float, ly2: float,
                          rx: float, ry: float, rw: float, rh: float) -> bool:
    """Vérifier si une ligne intersecte un rectangle"""
    # Implémentation simplifiée
    # Vérifier si un des points est dans le rectangle
    if point_in_rect(lx1, ly1, rx, ry, rw, rh) or point_in_rect(lx2, ly2, rx, ry, rw, rh):
        return True
    
    # Vérifier les intersections avec les bords
    # (implémentation simplifiée - à améliorer si nécessaire)
    return False
