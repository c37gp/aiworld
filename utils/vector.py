"""
Classe Vector2 - Vecteur 2D pour les positions et calculs géométriques
"""

import math
from typing import Tuple, Union


class Vector2:
    """
    Représente un vecteur 2D avec des opérations mathématiques.
    """
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        """Initialiser le vecteur"""
        self.x = float(x)
        self.y = float(y)
    
    def __repr__(self) -> str:
        return f"Vector2({self.x:.2f}, {self.y:.2f})"
    
    def __str__(self) -> str:
        return f"({self.x:.2f}, {self.y:.2f})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector2):
            return False
        return abs(self.x - other.x) < 1e-6 and abs(self.y - other.y) < 1e-6
    
    def __add__(self, other: Union["Vector2", Tuple[float, float]]) -> "Vector2":
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)
        elif isinstance(other, (tuple, list)) and len(other) == 2:
            return Vector2(self.x + other[0], self.y + other[1])
        else:
            raise TypeError(f"Unsupported operand type: {type(other)}")
    
    def __sub__(self, other: Union["Vector2", Tuple[float, float]]) -> "Vector2":
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x, self.y - other.y)
        elif isinstance(other, (tuple, list)) and len(other) == 2:
            return Vector2(self.x - other[0], self.y - other[1])
        else:
            raise TypeError(f"Unsupported operand type: {type(other)}")
    
    def __mul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: float) -> "Vector2":
        return Vector2(self.x / scalar, self.y / scalar)
    
    def __neg__(self) -> "Vector2":
        return Vector2(-self.x, -self.y)
    
    def __abs__(self) -> "Vector2":
        return Vector2(abs(self.x), abs(self.y))
    
    def __iadd__(self, other: Union["Vector2", Tuple[float, float]]) -> "Vector2":
        if isinstance(other, Vector2):
            self.x += other.x
            self.y += other.y
        elif isinstance(other, (tuple, list)) and len(other) == 2:
            self.x += other[0]
            self.y += other[1]
        else:
            raise TypeError(f"Unsupported operand type: {type(other)}")
        return self
    
    def __isub__(self, other: Union["Vector2", Tuple[float, float]]) -> "Vector2":
        if isinstance(other, Vector2):
            self.x -= other.x
            self.y -= other.y
        elif isinstance(other, (tuple, list)) and len(other) == 2:
            self.x -= other[0]
            self.y -= other[1]
        else:
            raise TypeError(f"Unsupported operand type: {type(other)}")
        return self
    
    def __imul__(self, scalar: float) -> "Vector2":
        self.x *= scalar
        self.y *= scalar
        return self
    
    def __itruediv__(self, scalar: float) -> "Vector2":
        self.x /= scalar
        self.y /= scalar
        return self
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convertir en tuple"""
        return (self.x, self.y)
    
    def to_int_tuple(self) -> Tuple[int, int]:
        """Convertir en tuple d'entiers"""
        return (int(self.x), int(self.y))
    
    def copy(self) -> "Vector2":
        """Créer une copie du vecteur"""
        return Vector2(self.x, self.y)
    
    def length(self) -> float:
        """Calculer la longueur (magnitude) du vecteur"""
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def length_squared(self) -> float:
        """Calculer le carré de la longueur (plus rapide)"""
        return self.x * self.x + self.y * self.y
    
    def normalize(self) -> "Vector2":
        """Normaliser le vecteur (le rendre de longueur 1)"""
        length = self.length()
        if length > 0:
            return self / length
        return Vector2(0, 0)
    
    def normalized(self) -> "Vector2":
        """Retourner une version normalisée du vecteur"""
        return self.normalize()
    
    def distance_to(self, other: "Vector2") -> float:
        """Calculer la distance vers un autre vecteur"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def distance_squared_to(self, other: "Vector2") -> float:
        """Calculer le carré de la distance vers un autre vecteur"""
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2
    
    def dot(self, other: "Vector2") -> float:
        """Calculer le produit scalaire avec un autre vecteur"""
        return self.x * other.x + self.y * other.y
    
    def cross(self, other: "Vector2") -> float:
        """Calculer le produit vectoriel (en 2D, retourne un scalaire)"""
        return self.x * other.y - self.y * other.x
    
    def angle(self) -> float:
        """Obtenir l'angle en radians (par rapport à l'axe X)"""
        return math.atan2(self.y, self.x)
    
    def angle_degrees(self) -> float:
        """Obtenir l'angle en degrés"""
        return math.degrees(self.angle())
    
    def rotate(self, angle_rad: float) -> "Vector2":
        """Tourner le vecteur d'un angle (en radians)"""
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return Vector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )
    
    def rotate_degrees(self, angle_deg: float) -> "Vector2":
        """Tourner le vecteur d'un angle (en degrés)"""
        return self.rotate(math.radians(angle_deg))
    
    def lerp(self, other: "Vector2", t: float) -> "Vector2":
        """Interpolation linéaire vers un autre vecteur"""
        return Vector2(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t
        )
    
    def clamp(self, min_val: float, max_val: float) -> "Vector2":
        """Limiter les composantes du vecteur"""
        return Vector2(
            max(min_val, min(max_val, self.x)),
            max(min_val, min(max_val, self.y))
        )
    
    def is_zero(self, epsilon: float = 1e-6) -> bool:
        """Vérifier si le vecteur est nul (ou très proche)"""
        return self.length_squared() < epsilon * epsilon
    
    @classmethod
    def zero(cls) -> "Vector2":
        """Créer un vecteur nul"""
        return cls(0, 0)
    
    @classmethod
    def one(cls) -> "Vector2":
        """Créer un vecteur (1, 1)"""
        return cls(1, 1)
    
    @classmethod
    def up(cls) -> "Vector2":
        """Créer un vecteur vers le haut"""
        return cls(0, -1)
    
    @classmethod
    def down(cls) -> "Vector2":
        """Créer un vecteur vers le bas"""
        return cls(0, 1)
    
    @classmethod
    def left(cls) -> "Vector2":
        """Créer un vecteur vers la gauche"""
        return cls(-1, 0)
    
    @classmethod
    def right(cls) -> "Vector2":
        """Créer un vecteur vers la droite"""
        return cls(1, 0)
    
    @classmethod
    def from_angle(cls, angle_rad: float, length: float = 1.0) -> "Vector2":
        """Créer un vecteur à partir d'un angle (en radians)"""
        return cls(length * math.cos(angle_rad), length * math.sin(angle_rad))
    
    @classmethod
    def from_angle_degrees(cls, angle_deg: float, length: float = 1.0) -> "Vector2":
        """Créer un vecteur à partir d'un angle (en degrés)"""
        return cls.from_angle(math.radians(angle_deg), length)


class Distance:
    """
    Classe utilitaire pour les calculs de distance.
    """
    
    @staticmethod
    def euclidean(a: Vector2, b: Vector2) -> float:
        """Distance euclidienne entre deux points"""
        return a.distance_to(b)
    
    @staticmethod
    def manhattan(a: Vector2, b: Vector2) -> float:
        """Distance de Manhattan entre deux points"""
        return abs(a.x - b.x) + abs(a.y - b.y)
    
    @staticmethod
    def chebyshev(a: Vector2, b: Vector2) -> float:
        """Distance de Chebyshev entre deux points"""
        return max(abs(a.x - b.x), abs(a.y - b.y))
    
    @staticmethod
    def squared(a: Vector2, b: Vector2) -> float:
        """Carré de la distance euclidienne"""
        return a.distance_squared_to(b)
