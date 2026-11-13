"""
Classe Renderer - Rendu graphique pour AI World
"""

import pygame
import sys
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from ..config import config
from ..utils.vector import Vector2
from ..utils.logger import Logger
from ..world.world import World, Resource, Structure, TerrainType, ResourceType
from ..agents.ai_agent import AIAgent, AgentState
from ..agents.needs import NeedType


@dataclass
class Camera:
    """Caméra pour la vue du monde"""
    position: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    zoom: float = 1.0
    
    def move(self, dx: float, dy: float):
        """Déplacer la caméra"""
        self.position.x += dx / self.zoom
        self.position.y += dy / self.zoom
    
    def set_position(self, x: float, y: float):
        """Définir la position de la caméra"""
        self.position.x = x
        self.position.y = y
    
    def zoom_in(self, amount: float = 0.1):
        """Zoom avant"""
        self.zoom = min(3.0, self.zoom + amount)
    
    def zoom_out(self, amount: float = 0.1):
        """Zoom arrière"""
        self.zoom = max(0.1, self.zoom - amount)
    
    def get_world_to_screen(self, world_pos: Vector2) -> Vector2:
        """Convertir les coordonnées monde en coordonnées écran"""
        screen_x = (world_pos.x - self.position.x) * self.zoom
        screen_y = (world_pos.y - self.position.y) * self.zoom
        return Vector2(screen_x, screen_y)
    
    def get_screen_to_world(self, screen_pos: Vector2) -> Vector2:
        """Convertir les coordonnées écran en coordonnées monde"""
        world_x = screen_pos.x / self.zoom + self.position.x
        world_y = screen_pos.y / self.zoom + self.position.y
        return Vector2(world_x, world_y)


class Renderer:
    """
    Rendu graphique pour AI World.
    Gère l'affichage du monde, des agents, des ressources et de l'UI.
    """
    
    def __init__(self, world: World):
        """Initialiser le rendu"""
        self.world = world
        self.logger = Logger("Renderer")
        
        # Initialiser Pygame
        pygame.init()
        
        # Créer la fenêtre
        self.screen_width, self.screen_height = config.ui.get_screen_size()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("AI World - Simulation")
        
        # Caméra
        self.camera = Camera(
            position=Vector2(world.width / 2, world.height / 2),
            zoom=1.0
        )
        
        # Polices
        self.fonts = {
            "small": pygame.font.SysFont(config.ui.font_name, config.ui.font_size),
            "medium": pygame.font.SysFont(config.ui.font_name, config.ui.font_size + 4),
            "large": pygame.font.SysFont(config.ui.font_name, config.ui.font_size + 8),
            "title": pygame.font.SysFont(config.ui.font_name, config.ui.font_size + 12, bold=True)
        }
        
        # Couleurs
        self.colors = {
            "background": config.ui.background,
            "panel": config.ui.panel_background,
            "text": config.ui.text_color,
            "highlight": config.ui.highlight_color,
            "danger": config.ui.danger_color,
            "success": config.ui.success_color,
            
            # Couleurs du terrain
            "grass": (50, 150, 50),
            "sand": (200, 180, 100),
            "water": (50, 100, 200),
            "mountain": (100, 100, 100),
            "forest": (30, 100, 30),
            "rock": (120, 120, 120),
            
            # Couleurs des ressources
            "food": (0, 200, 0),
            "wood": (139, 69, 19),
            "stone": (150, 150, 150),
            "metal": (180, 180, 180),
            "water": (0, 150, 255),
            "gold": (255, 215, 0)
        }
        
        # Mini-map
        self.mini_map_size = config.ui.mini_map_size
        self.mini_map_scale = self.mini_map_size / max(world.width, world.height)
        
        # FPS
        self.clock = pygame.time.Clock()
        self.fps = config.ui.fps
        
        # État du rendu
        self.show_grid = False
        self.show_mini_map = True
        self.show_stats = True
    
    def render(self, agents: List[AIAgent], selected_agent: Optional[AIAgent] = None,
               paused: bool = False, time_scale: float = 1.0):
        """Rendre une frame complète"""
        # Effacer l'écran
        self.screen.fill(self.colors["background"])
        
        # Rendre le monde
        self._render_world()
        
        # Rendre les ressources
        self._render_resources()
        
        # Rendre les structures
        self._render_structures()
        
        # Rendre les agents
        self._render_agents(agents, selected_agent)
        
        # Rendre l'UI
        self._render_ui(agents, selected_agent, paused, time_scale)
        
        # Rendre la mini-map
        if self.show_mini_map:
            self._render_mini_map(agents, selected_agent)
        
        # Mettre à jour l'affichage
        pygame.display.flip()
        
        # Limiter les FPS
        self.clock.tick(self.fps)
    
    def _render_world(self):
        """Rendre le monde (terrain)"""
        tile_size = config.world.tile_size
        
        # Calculer la zone visible
        top_left = self.camera.get_world_to_screen(Vector2(0, 0))
        bottom_right = self.camera.get_world_to_screen(
            Vector2(self.world.width, self.world.height)
        )
        
        # Dessiner le terrain
        for x in range(0, self.world.width, tile_size):
            for y in range(0, self.world.height, tile_size):
                cell = self.world.get_cell_at(Vector2(x, y))
                
                # Convertir en coordonnées écran
                screen_pos = self.camera.get_world_to_screen(Vector2(x, y))
                
                # Vérifier si la cellule est visible
                if (screen_pos.x < -tile_size * self.camera.zoom or 
                    screen_pos.x > self.screen_width + tile_size * self.camera.zoom or
                    screen_pos.y < -tile_size * self.camera.zoom or 
                    screen_pos.y > self.screen_height + tile_size * self.camera.zoom):
                    continue
                
                # Dessiner la cellule
                color = self._get_terrain_color(cell.cell_type)
                
                pygame.draw.rect(
                    self.screen,
                    color,
                    (screen_pos.x, screen_pos.y, tile_size * self.camera.zoom, tile_size * self.camera.zoom)
                )
                
                # Dessiner la grille
                if self.show_grid:
                    pygame.draw.rect(
                        self.screen,
                        (80, 80, 80),
                        (screen_pos.x, screen_pos.y, tile_size * self.camera.zoom, tile_size * self.camera.zoom),
                        1
                    )
    
    def _get_terrain_color(self, cell_type: TerrainType) -> Tuple[int, int, int]:
        """Obtenir la couleur d'un type de cellule"""
        colors = {
            TerrainType.GRASS: self.colors["grass"],
            TerrainType.SAND: self.colors["sand"],
            TerrainType.WATER: self.colors["water"],
            TerrainType.MOUNTAIN: self.colors["mountain"],
            TerrainType.FOREST: self.colors["forest"],
            TerrainType.ROCK: self.colors["rock"]
        }
        return colors.get(cell_type, (100, 100, 100))
    
    def _render_resources(self):
        """Rendre les ressources"""
        for resource in self.world.resources.values():
            screen_pos = self.camera.get_world_to_screen(resource.position)
            
            # Vérifier si la ressource est visible
            if (screen_pos.x < -20 or screen_pos.x > self.screen_width + 20 or
                screen_pos.y < -20 or screen_pos.y > self.screen_height + 20):
                continue
            
            # Obtenir la couleur de la ressource
            color = self._get_resource_color(resource.resource_type)
            
            # Dessiner la ressource
            size = 8 * self.camera.zoom
            pygame.draw.circle(
                self.screen,
                color,
                (int(screen_pos.x), int(screen_pos.y)),
                int(size)
            )
            
            # Dessiner un contour
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (int(screen_pos.x), int(screen_pos.y)),
                int(size),
                1
            )
            
            # Dessiner une icône ou un label si le zoom est suffisant
            if self.camera.zoom > 0.5:
                label = resource.resource_type.name[0]
                font = self.fonts["small"]
                text = font.render(label, True, (255, 255, 255))
                self.screen.blit(text, (screen_pos.x + size + 2, screen_pos.y - 8))
    
    def _get_resource_color(self, resource_type: ResourceType) -> Tuple[int, int, int]:
        """Obtenir la couleur d'un type de ressource"""
        colors = {
            ResourceType.FOOD: self.colors["food"],
            ResourceType.WOOD: self.colors["wood"],
            ResourceType.STONE: self.colors["stone"],
            ResourceType.METAL: self.colors["metal"],
            ResourceType.WATER: self.colors["water"],
            ResourceType.GOLD: self.colors["gold"]
        }
        return colors.get(resource_type, (200, 200, 200))
    
    def _render_structures(self):
        """Rendre les structures"""
        for structure in self.world.structures.values():
            screen_pos = self.camera.get_world_to_screen(structure.position)
            
            # Vérifier si la structure est visible
            if (screen_pos.x < -50 or screen_pos.x > self.screen_width + 50 or
                screen_pos.y < -50 or screen_pos.y > self.screen_height + 50):
                continue
            
            # Dessiner la structure
            width = structure.size[0] * self.camera.zoom
            height = structure.size[1] * self.camera.zoom
            
            # Couleur en fonction du type
            if structure.structure_type == "house":
                color = (150, 100, 50)
            elif structure.structure_type == "farm":
                color = (100, 150, 50)
            elif structure.structure_type == "mine":
                color = (100, 100, 100)
            elif structure.structure_type == "tower":
                color = (120, 120, 120)
            else:
                color = (120, 120, 120)
            
            pygame.draw.rect(
                self.screen,
                color,
                (screen_pos.x - width / 2, screen_pos.y - height / 2, width, height)
            )
            
            # Dessiner un contour
            pygame.draw.rect(
                self.screen,
                (200, 200, 200),
                (screen_pos.x - width / 2, screen_pos.y - height / 2, width, height),
                1
            )
            
            # Dessiner la barre de santé
            if structure.health < structure.max_health:
                self._draw_health_bar(
                    screen_pos.x, screen_pos.y - height / 2 - 5,
                    width, 3,
                    structure.health / structure.max_health
                )
    
    def _render_agents(self, agents: List[AIAgent], selected_agent: Optional[AIAgent]):
        """Rendre les agents"""
        for agent in agents:
            if agent.state == AgentState.DEAD:
                continue
            
            screen_pos = self.camera.get_world_to_screen(agent.position)
            
            # Vérifier si l'agent est visible
            if (screen_pos.x < -30 or screen_pos.x > self.screen_width + 30 or
                screen_pos.y < -30 or screen_pos.y > self.screen_height + 30):
                continue
            
            # Dessiner l'agent
            size = agent.size * self.camera.zoom
            
            # Dessiner le corps
            pygame.draw.circle(
                self.screen,
                agent.color,
                (int(screen_pos.x), int(screen_pos.y)),
                int(size)
            )
            
            # Dessiner un contour
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (int(screen_pos.x), int(screen_pos.y)),
                int(size),
                1
            )
            
            # Dessiner la barre de santé
            self._draw_health_bar(
                screen_pos.x - size, screen_pos.y + size + 3,
                size * 2, 3,
                agent.health / agent.max_health
            )
            
            # Dessiner la barre d'énergie
            energy = agent.needs.get_need(NeedType.ENERGY).current
            max_energy = agent.needs.get_need(NeedType.ENERGY).max_value
            self._draw_health_bar(
                screen_pos.x - size, screen_pos.y + size + 7,
                size * 2, 2,
                energy / max_energy,
                (0, 200, 0), (50, 50, 50)
            )
            
            # Dessiner un indicateur de leader
            if agent.is_leader:
                pygame.draw.circle(
                    self.screen,
                    (255, 215, 0),
                    (int(screen_pos.x), int(screen_pos.y)),
                    int(size + 3),
                    2
                )
            
            # Dessiner un indicateur d'état
            state_colors = {
                AgentState.IDLE: (100, 100, 100),
                AgentState.MOVING: (0, 255, 0),
                AgentState.GATHERING: (255, 255, 0),
                AgentState.BUILDING: (0, 0, 255),
                AgentState.FIGHTING: (255, 0, 0),
                AgentState.TRADING: (255, 0, 255),
                AgentState.SOCIALIZING: (0, 255, 255),
                AgentState.RESTING: (100, 50, 0),
                AgentState.EXPLORING: (50, 150, 50),
                AgentState.DEAD: (0, 0, 0)
            }
            
            state_color = state_colors.get(agent.state, (100, 100, 100))
            pygame.draw.circle(
                self.screen,
                state_color,
                (int(screen_pos.x), int(screen_pos.y) - int(size) - 5),
                3
            )
            
            # Dessiner le nom si l'agent est sélectionné ou si le zoom est suffisant
            if agent == selected_agent or self.camera.zoom > 0.8:
                font = self.fonts["small"]
                text = font.render(agent.name, True, (255, 255, 255))
                self.screen.blit(text, (screen_pos.x + size + 5, screen_pos.y - 10))
            
            # Dessiner une bordure si l'agent est sélectionné
            if agent == selected_agent:
                pygame.draw.circle(
                    self.screen,
                    (255, 255, 0),
                    (int(screen_pos.x), int(screen_pos.y)),
                    int(size + 5),
                    2
                )
    
    def _draw_health_bar(self, x: float, y: float, width: float, height: float,
                        percent: float, color: Tuple[int, int, int] = (0, 255, 0),
                        background: Tuple[int, int, int] = (50, 50, 50)):
        """Dessiner une barre de santé/progression"""
        # Dessiner le fond
        pygame.draw.rect(
            self.screen,
            background,
            (x, y, width, height)
        )
        
        # Dessiner la barre
        pygame.draw.rect(
            self.screen,
            color,
            (x, y, width * percent, height)
        )
    
    def _render_ui(self, agents: List[AIAgent], selected_agent: Optional[AIAgent],
                   paused: bool, time_scale: float):
        """Rendre l'interface utilisateur"""
        # Dessiner le panneau d'information
        panel_width = config.ui.info_panel_width
        panel_height = self.screen_height
        
        pygame.draw.rect(
            self.screen,
            self.colors["panel"],
            (self.screen_width - panel_width, 0, panel_width, panel_height)
        )
        
        # Dessiner la bordure du panneau
        pygame.draw.rect(
            self.screen,
            (100, 100, 100),
            (self.screen_width - panel_width, 0, panel_width, panel_height),
            1
        )
        
        # Titre
        title = self.fonts["title"].render("AI World", True, self.colors["text"])
        self.screen.blit(title, (self.screen_width - panel_width + 10, 10))
        
        # Statistiques du monde
        y_offset = 40
        
        # Temps de simulation
        time_text = self.fonts["medium"].render(
            f"Temps: {self.world.time_manager.get_date_string()}",
            True, self.colors["text"]
        )
        self.screen.blit(time_text, (self.screen_width - panel_width + 10, y_offset))
        y_offset += 25
        
        # Nombre d'agents
        agent_text = self.fonts["medium"].render(
            f"Agents: {len(agents)}",
            True, self.colors["text"]
        )
        self.screen.blit(agent_text, (self.screen_width - panel_width + 10, y_offset))
        y_offset += 25
        
        # Ressources
        resource_text = self.fonts["medium"].render(
            f"Ressources: {len(self.world.resources)}",
            True, self.colors["text"]
        )
        self.screen.blit(resource_text, (self.screen_width - panel_width + 10, y_offset))
        y_offset += 25
        
        # Structures
        structure_text = self.fonts["medium"].render(
            f"Structures: {len(self.world.structures)}",
            True, self.colors["text"]
        )
        self.screen.blit(structure_text, (self.screen_width - panel_width + 10, y_offset))
        y_offset += 30
        
        # Contrôles
        controls_text = self.fonts["medium"].render("Contrôles:", True, self.colors["text"])
        self.screen.blit(controls_text, (self.screen_width - panel_width + 10, y_offset))
        y_offset += 25
        
        control_lines = [
            "WASD: Déplacer la caméra",
            "Molette: Zoomer",
            "Clic gauche: Sélectionner",
            "Espace: Pause",
            "1-5: Vitesse du temps",
            "G: Afficher la grille",
            "M: Afficher la mini-map"
        ]
        
        for line in control_lines:
            text = self.fonts["small"].render(line, True, self.colors["text"])
            self.screen.blit(text, (self.screen_width - panel_width + 15, y_offset))
            y_offset += 20
        
        # État de la simulation
        y_offset += 10
        status_text = self.fonts["medium"].render(
            f"État: {'PAUSE' if paused else 'EN COURS'}",
            True, self.colors["text"]
        )
        self.screen.blit(status_text, (self.screen_width - panel_width + 10, y_offset))
        y_offset += 25
        
        speed_text = self.fonts["medium"].render(
            f"Vitesse: {time_scale:.1f}x",
            True, self.colors["text"]
        )
        self.screen.blit(speed_text, (self.screen_width - panel_width + 10, y_offset))
        
        # Informations sur l'agent sélectionné
        if selected_agent:
            y_offset += 40
            
            # Séparateur
            pygame.draw.line(
                self.screen,
                (150, 150, 150),
                (self.screen_width - panel_width + 10, y_offset - 10),
                (self.screen_width - 10, y_offset - 10),
                1
            )
            
            # Titre
            name_text = self.fonts["large"].render(
                f"Agent: {selected_agent.name}",
                True, self.colors["text"]
            )
            self.screen.blit(name_text, (self.screen_width - panel_width + 10, y_offset))
            y_offset += 30
            
            # Type d'IA
            type_text = self.fonts["medium"].render(
                f"Type: {selected_agent.ai_type.name}",
                True, self.colors["text"]
            )
            self.screen.blit(type_text, (self.screen_width - panel_width + 10, y_offset))
            y_offset += 25
            
            # État
            state_text = self.fonts["medium"].render(
                f"État: {selected_agent.state.name}",
                True, self.colors["text"]
            )
            self.screen.blit(state_text, (self.screen_width - panel_width + 10, y_offset))
            y_offset += 25
            
            # Santé
            health_text = self.fonts["medium"].render(
                f"Santé: {selected_agent.health:.1f}/{selected_agent.max_health:.1f}",
                True, self.colors["text"]
            )
            self.screen.blit(health_text, (self.screen_width - panel_width + 10, y_offset))
            y_offset += 25
            
            # Énergie
            energy = selected_agent.needs.get_need(NeedType.ENERGY).current
            max_energy = selected_agent.needs.get_need(NeedType.ENERGY).max_value
            energy_text = self.fonts["medium"].render(
                f"Énergie: {energy:.1f}/{max_energy:.1f}",
                True, self.colors["text"]
            )
            self.screen.blit(energy_text, (self.screen_width - panel_width + 10, y_offset))
            y_offset += 25
            
            # Âge
            age_text = self.fonts["medium"].render(
                f"Âge: {selected_agent.age:.1f}/{selected_agent.max_age:.1f}",
                True, self.colors["text"]
            )
            self.screen.blit(age_text, (self.screen_width - panel_width + 10, y_offset))
            y_offset += 25
            
            # Personnalité
            personality = selected_agent.personality.get_personality_summary()
            personality_text = self.fonts["medium"].render(
                f"Personnalité: {personality}",
                True, self.colors["text"]
            )
            self.screen.blit(personality_text, (self.screen_width - panel_width + 10, y_offset))
            y_offset += 25
            
            # Groupe
            if selected_agent.group_id:
                group_text = self.fonts["medium"].render(
                    f"Groupe: {selected_agent.group_id}",
                    True, self.colors["text"]
                )
                self.screen.blit(group_text, (self.screen_width - panel_width + 10, y_offset))
                y_offset += 25
            
            # Objectif actif
            active_goal = selected_agent.goals.get_active_goal()
            if active_goal:
                goal_text = self.fonts["medium"].render(
                    f"Objectif: {active_goal.description}",
                    True, self.colors["text"]
                )
                self.screen.blit(goal_text, (self.screen_width - panel_width + 10, y_offset))
    
    def _render_mini_map(self, agents: List[AIAgent], selected_agent: Optional[AIAgent]):
        """Rendre la mini-map"""
        # Position de la mini-map
        map_x = self.screen_width - config.ui.info_panel_width - self.mini_map_size - 10
        map_y = self.screen_height - self.mini_map_size - 10
        
        # Dessiner le fond
        pygame.draw.rect(
            self.screen,
            (30, 30, 40),
            (map_x, map_y, self.mini_map_size, self.mini_map_size)
        )
        
        # Dessiner la bordure
        pygame.draw.rect(
            self.screen,
            (100, 100, 100),
            (map_x, map_y, self.mini_map_size, self.mini_map_size),
            1
        )
        
        # Dessiner le monde en miniature
        for x in range(0, self.world.width, 20):
            for y in range(0, self.world.height, 20):
                cell = self.world.get_cell_at(Vector2(x, y))
                color = self._get_terrain_color(cell.cell_type)
                
                # Convertir en coordonnées de la mini-map
                mm_x = map_x + x * self.mini_map_scale
                mm_y = map_y + y * self.mini_map_scale
                
                pygame.draw.rect(
                    self.screen,
                    color,
                    (mm_x, mm_y, 20 * self.mini_map_scale, 20 * self.mini_map_scale)
                )
        
        # Dessiner les ressources
        for resource in self.world.resources.values():
            mm_x = map_x + resource.position.x * self.mini_map_scale
            mm_y = map_y + resource.position.y * self.mini_map_scale
            color = self._get_resource_color(resource.resource_type)
            
            pygame.draw.circle(
                self.screen,
                color,
                (int(mm_x), int(mm_y)),
                2
            )
        
        # Dessiner les structures
        for structure in self.world.structures.values():
            mm_x = map_x + structure.position.x * self.mini_map_scale
            mm_y = map_y + structure.position.y * self.mini_map_scale
            
            pygame.draw.rect(
                self.screen,
                (200, 200, 200),
                (mm_x - 2, mm_y - 2, 4, 4)
            )
        
        # Dessiner les agents
        for agent in agents:
            if agent.state == AgentState.DEAD:
                continue
            
            mm_x = map_x + agent.position.x * self.mini_map_scale
            mm_y = map_y + agent.position.y * self.mini_map_scale
            
            pygame.draw.circle(
                self.screen,
                agent.color,
                (int(mm_x), int(mm_y)),
                2
            )
        
        # Dessiner la zone visible de la caméra
        cam_x = map_x + self.camera.position.x * self.mini_map_scale
        cam_y = map_y + self.camera.position.y * self.mini_map_scale
        cam_width = (self.screen_width / self.camera.zoom) * self.mini_map_scale
        cam_height = (self.screen_height / self.camera.zoom) * self.mini_map_scale
        
        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            (cam_x, cam_y, cam_width, cam_height),
            1
        )
        
        # Dessiner l'agent sélectionné
        if selected_agent:
            mm_x = map_x + selected_agent.position.x * self.mini_map_scale
            mm_y = map_y + selected_agent.position.y * self.mini_map_scale
            
            pygame.draw.circle(
                self.screen,
                (255, 255, 0),
                (int(mm_x), int(mm_y)),
                3
            )
    
    def handle_event(self, event: pygame.event.Event, agents: List[AIAgent],
                     selected_agent: Optional[AIAgent]) -> Tuple[Optional[AIAgent], bool, float]:
        """
        Gérer un événement Pygame.
        Retourne (nouvel_agent_sélectionné, pause, nouvelle_vitesse)
        """
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        elif event.type == pygame.KEYDOWN:
            # Déplacement de la caméra
            if event.key == pygame.K_w:
                self.camera.move(0, -20)
            elif event.key == pygame.K_s:
                self.camera.move(0, 20)
            elif event.key == pygame.K_a:
                self.camera.move(-20, 0)
            elif event.key == pygame.K_d:
                self.camera.move(20, 0)
            
            # Zoom
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                self.camera.zoom_in()
            elif event.key == pygame.K_MINUS:
                self.camera.zoom_out()
            
            # Afficher/masquer la grille
            elif event.key == pygame.K_g:
                self.show_grid = not self.show_grid
            
            # Afficher/masquer la mini-map
            elif event.key == pygame.K_m:
                self.show_mini_map = not self.show_mini_map
            
            # Pause
            elif event.key == pygame.K_SPACE:
                return (selected_agent, True, 1.0)  # Inverser la pause
            
            # Vitesse du temps
            elif event.key == pygame.K_1:
                return (selected_agent, False, 0.5)
            elif event.key == pygame.K_2:
                return (selected_agent, False, 1.0)
            elif event.key == pygame.K_3:
                return (selected_agent, False, 2.0)
            elif event.key == pygame.K_4:
                return (selected_agent, False, 5.0)
            elif event.key == pygame.K_5:
                return (selected_agent, False, 10.0)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                # Convertir les coordonnées de la souris en coordonnées monde
                mouse_pos = Vector2(event.pos[0], event.pos[1])
                world_pos = self.camera.get_screen_to_world(mouse_pos)
                
                # Trouver l'agent le plus proche
                closest_agent = None
                min_distance = float('inf')
                
                for agent in agents:
                    if agent.state == AgentState.DEAD:
                        continue
                    
                    distance = agent.position.distance_to(world_pos)
                    if distance < min_distance and distance < 50:  # Rayon de sélection
                        min_distance = distance
                        closest_agent = agent
                
                if closest_agent:
                    return (closest_agent, False, 1.0)
            
            elif event.button == 4:  # Molette vers le haut
                self.camera.zoom_in()
            elif event.button == 5:  # Molette vers le bas
                self.camera.zoom_out()
        
        elif event.type == pygame.MOUSEMOTION:
            # Déplacement de la caméra avec la souris (si bouton maintenu)
            if event.buttons[0]:  # Bouton gauche maintenu
                self.camera.move(-event.rel[0] / self.camera.zoom, -event.rel[1] / self.camera.zoom)
            elif event.buttons[2]:  # Bouton droit maintenu
                self.camera.move(-event.rel[0] / self.camera.zoom, -event.rel[1] / self.camera.zoom)
        
        return (selected_agent, False, 1.0)
    
    def get_camera(self) -> Camera:
        """Obtenir la caméra"""
        return self.camera
    
    def set_camera_position(self, x: float, y: float):
        """Définir la position de la caméra"""
        self.camera.set_position(x, y)
    
    def reset_camera(self):
        """Réinitialiser la caméra"""
        self.camera.position = Vector2(self.world.width / 2, self.world.height / 2)
        self.camera.zoom = 1.0
