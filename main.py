"""
AI World - Simulation 2D d'IA autonomes

Point d'entrée principal pour la simulation.
"""

import sys
import time
import random
from typing import Dict, List, Optional, Any

import pygame

from .config import config, AIType, SimulationMode
from .world.world import World, ResourceType
from .agents.ai_agent import AIAgent, AgentState
from .systems.communication import CommunicationSystem
from .systems.social import SocialSystem
from .systems.construction import ConstructionSystem
from .systems.trade import TradeSystem
from .systems.combat import CombatSystem
from .systems.knowledge import KnowledgeSystem
from .systems.reproduction import ReproductionSystem
from .ui.renderer import Renderer
from .utils.logger import Logger
from .utils.history import history_manager
from .utils.event_bus import event_bus


class Simulation:
    """
    Classe principale de la simulation AI World.
    Gère le monde, les agents et les systèmes.
    """
    
    def __init__(self):
        """Initialiser la simulation"""
        self.logger = Logger("Simulation")
        
        # Monde
        self.world = World()
        
        # Systèmes
        self.communication_system = CommunicationSystem()
        self.social_system = SocialSystem(self.communication_system)
        self.construction_system = ConstructionSystem(self.world)
        self.trade_system = TradeSystem()
        self.combat_system = CombatSystem()
        self.knowledge_system = KnowledgeSystem()
        self.reproduction_system = ReproductionSystem(self.world)
        
        # Agents
        self.agents: Dict[str, AIAgent] = {}
        self.agent_counter = 0
        
        # Interface utilisateur
        self.renderer = Renderer(self.world)
        
        # État de la simulation
        self.running = True
        self.paused = False
        self.time_scale = 1.0
        self.simulation_mode = SimulationMode.REAL_TIME
        
        # Agent sélectionné
        self.selected_agent: Optional[AIAgent] = None
        
        # Statistiques
        self.stats = {
            "total_agents": 0,
            "active_agents": 0,
            "dead_agents": 0,
            "start_time": time.time(),
            "last_update_time": time.time()
        }
        
        # Initialisation
        self._initialize()
    
    def _initialize(self):
        """Initialisation de la simulation"""
        # Créer les agents initiaux
        for i in range(config.world.initial_agents):
            self._create_agent()
        
        # Créer quelques groupes
        self._create_initial_groups()
        
        # Démarrer l'historique
        history_manager.add_entry(
            "simulation_started",
            data={"initial_agents": config.world.initial_agents},
            simulation_time=0
        )
        
        # Enregistrer les agents dans les systèmes
        for agent in self.agents.values():
            self.communication_system.register_agent(agent.agent_id)
        
        self.logger.info(f"Simulation initialisée avec {len(self.agents)} agents")
    
    def _create_agent(self, ai_type: AIType = AIType.BASIC, 
                      position: Any = None, name: str = None) -> AIAgent:
        """Créer un nouvel agent"""
        agent_id = f"agent_{self.agent_counter}"
        self.agent_counter += 1
        
        # Déterminer le type d'IA
        if ai_type == AIType.BASIC:
            # Choisir aléatoirement parmi les types disponibles
            types = [AIType.GPT, AIType.GEMINI, AIType.APERTUS]
            ai_type = random.choice(types)
        
        # Créer l'agent
        agent = AIAgent(
            world=self.world,
            position=position,
            ai_type=ai_type,
            agent_id=agent_id,
            name=name
        )
        
        # Ajouter à la liste
        self.agents[agent_id] = agent
        self.stats["total_agents"] += 1
        self.stats["active_agents"] += 1
        
        # Enregistrer dans les systèmes
        self.communication_system.register_agent(agent_id)
        
        # Ajouter à l'historique
        history_manager.add_entry(
            "agent_created",
            entity_id=agent_id,
            data={
                "name": agent.name,
                "ai_type": agent.ai_type.name,
                "position": agent.position.to_tuple()
            },
            simulation_time=self.world.time_manager.get_simulation_time()
        )
        
        self.logger.info(f"Agent créé: {agent.name} ({ai_type.name})")
        
        return agent
    
    def _create_initial_groups(self):
        """Créer des groupes initiaux"""
        # Créer 2-3 groupes aléatoires
        num_groups = random.randint(2, 3)
        
        # Mélanger les agents
        agent_list = list(self.agents.values())
        random.shuffle(agent_list)
        
        # Diviser en groupes
        group_size = len(agent_list) // num_groups
        
        for i in range(num_groups):
            start = i * group_size
            end = (i + 1) * group_size if i < num_groups - 1 else len(agent_list)
            
            group_agents = agent_list[start:end]
            
            if group_agents:
                # Le premier agent est le leader
                leader = group_agents[0]
                
                # Créer le groupe
                group_name = f"Groupe {i + 1}"
                group = self.social_system.create_group(leader, group_name)
                
                # Ajouter les autres agents au groupe
                for agent in group_agents[1:]:
                    self.social_system.join_group(agent, group.group_id)
    
    def run(self):
        """Exécuter la simulation"""
        self.logger.info("Démarrage de la simulation...")
        
        # Boucle principale
        while self.running:
            # Gérer les événements
            self._handle_events()
            
            # Mettre à jour la simulation
            if not self.paused:
                self._update()
            
            # Rendre
            self._render()
        
        # Nettoyage
        self._cleanup()
    
    def _handle_events(self):
        """Gérer les événements"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            else:
                # Gérer l'événement dans le renderer
                selected, pause_toggle, new_speed = self.renderer.handle_event(
                    event, list(self.agents.values()), self.selected_agent
                )
                
                # Mettre à jour l'agent sélectionné
                if selected:
                    self.selected_agent = selected
                
                # Mettre à jour la pause
                if pause_toggle:
                    self.paused = not self.paused
                
                # Mettre à jour la vitesse
                if new_speed != 1.0:
                    self.time_scale = new_speed
                    self.world.time_manager.set_time_scale(new_speed)
    
    def _update(self):
        """Mettre à jour la simulation"""
        # Calculer le delta_time
        current_time = time.time()
        delta_time = current_time - self.stats["last_update_time"]
        self.stats["last_update_time"] = current_time
        
        # Mettre à jour le monde
        self.world.update(delta_time)
        
        # Mettre à jour les systèmes
        self.communication_system.update(delta_time)
        self.social_system.update(delta_time)
        self.construction_system.update_projects(delta_time)
        self.combat_system.update_combats()
        self.knowledge_system.update(delta_time)
        self.reproduction_system.update(delta_time)
        
        # Mettre à jour les agents
        agents_to_remove = []
        
        for agent_id, agent in self.agents.items():
            # Mettre à jour l'agent
            agent.update(delta_time)
            
            # Traiter les messages
            self.communication_system.process_messages(agent)
            
            # Vérifier la mort
            if agent.state == AgentState.DEAD:
                agents_to_remove.append(agent_id)
            
            # Vérifier la reproduction
            if agent.reproduction_ready:
                # Essayer de se reproduire
                if random.random() < 0.01:  # Probabilité faible
                    child = self.reproduction_system.reproduce_asexual(agent)
                    if child:
                        self.agents[child.agent_id] = child
                        self.communication_system.register_agent(child.agent_id)
                        self.stats["active_agents"] += 1
                        
                        # Ajouter à l'historique
                        history_manager.add_entry(
                            "agent_born",
                            entity_id=child.agent_id,
                            data={
                                "parent_id": agent.agent_id,
                                "name": child.name,
                                "ai_type": child.ai_type.name
                            },
                            simulation_time=self.world.time_manager.get_simulation_time()
                        )
        
        # Supprimer les agents morts
        for agent_id in agents_to_remove:
            self._remove_agent(agent_id)
        
        # Mettre à jour l'historique
        history_manager.add_snapshot(
            agents=[a.get_status() for a in self.agents.values()],
            structures=[s.to_dict() for s in self.world.structures.values()],
            resources=[{
                "id": r_id,
                "type": r.resource_type.name,
                "amount": r.amount,
                "position": r.position.to_tuple()
            } for r_id, r in self.world.resources.items()],
            groups=[],
            stats=self._get_stats(),
            simulation_time=self.world.time_manager.get_simulation_time()
        )
        
        # Vérifier les événements aléatoires
        self._check_random_events()
    
    def _check_random_events(self):
        """Vérifier les événements aléatoires"""
        if random.random() < config.simulation.random_event_probability:
            self._generate_random_event()
    
    def _generate_random_event(self):
        """Générer un événement aléatoire"""
        event_type = random.choice([
            "resource_spawn",
            "disaster",
            "bonus",
            "conflict"
        ])
        
        if event_type == "resource_spawn":
            # Faire apparaître une nouvelle ressource
            position = self.world.get_random_spawn_position()
            self.world._spawn_resource(position)
            
            history_manager.add_entry(
                "resource_spawned",
                data={"position": position.to_tuple()},
                simulation_time=self.world.time_manager.get_simulation_time()
            )
        
        elif event_type == "disaster":
            # Désastre naturel (foudre, tremblement de terre, etc.)
            # Pour l'instant, infliger des dégâts à un agent aléatoire
            if self.agents:
                agent = random.choice(list(self.agents.values()))
                agent.take_damage(random.uniform(10, 30))
                
                history_manager.add_entry(
                    "disaster",
                    entity_id=agent.agent_id,
                    data={"type": "lightning", "damage": 20},
                    simulation_time=self.world.time_manager.get_simulation_time()
                )
        
        elif event_type == "bonus":
            # Bonus pour un agent aléatoire
            if self.agents:
                agent = random.choice(list(self.agents.values()))
                agent.needs.gain_energy(50)
                
                history_manager.add_entry(
                    "bonus",
                    entity_id=agent.agent_id,
                    data={"type": "energy", "amount": 50},
                    simulation_time=self.world.time_manager.get_simulation_time()
                )
        
        elif event_type == "conflict":
            # Créer un conflit entre deux agents
            if len(self.agents) >= 2:
                agents = list(self.agents.values())
                agent1 = random.choice(agents)
                agent2 = random.choice(agents)
                
                if agent1 != agent2:
                    # Démarrer un combat
                    combat = self.combat_system.start_combat(agent1, agent2)
                    
                    history_manager.add_entry(
                        "combat_started",
                        data={
                            "attacker_id": agent1.agent_id,
                            "defender_id": agent2.agent_id
                        },
                        simulation_time=self.world.time_manager.get_simulation_time()
                    )
    
    def _remove_agent(self, agent_id: str):
        """Supprimer un agent"""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        
        # Désenregistrer des systèmes
        self.communication_system.unregister_agent(agent_id)
        
        # Supprimer de l'agent sélectionné
        if self.selected_agent == agent:
            self.selected_agent = None
        
        # Supprimer de la liste
        del self.agents[agent_id]
        
        # Mettre à jour les statistiques
        self.stats["active_agents"] -= 1
        self.stats["dead_agents"] += 1
        
        # Ajouter à l'historique
        history_manager.add_entry(
            "agent_died",
            entity_id=agent_id,
            data={"name": agent.name, "age": agent.age},
            simulation_time=self.world.time_manager.get_simulation_time()
        )
        
        self.logger.info(f"Agent supprimé: {agent.name}")
    
    def _render(self):
        """Rendre la simulation"""
        self.renderer.render(
            list(self.agents.values()),
            self.selected_agent,
            self.paused,
            self.time_scale
        )
    
    def _get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques de la simulation"""
        return {
            "simulation_time": self.world.time_manager.get_simulation_time(),
            "total_agents": self.stats["total_agents"],
            "active_agents": self.stats["active_agents"],
            "dead_agents": self.stats["dead_agents"],
            "resources": len(self.world.resources),
            "structures": len(self.world.structures),
            "groups": len(self.social_system.groups),
            "combats": len(self.combat_system.combats)
        }
    
    def _cleanup(self):
        """Nettoyer les ressources"""
        pygame.quit()
        self.logger.info("Simulation terminée")
    
    def create_agent_with_type(self, ai_type: AIType) -> AIAgent:
        """Créer un agent avec un type d'IA spécifique"""
        return self._create_agent(ai_type=ai_type)
    
    def get_agent(self, agent_id: str) -> Optional[AIAgent]:
        """Obtenir un agent"""
        return self.agents.get(agent_id)
    
    def get_agents(self) -> List[AIAgent]:
        """Obtenir tous les agents"""
        return list(self.agents.values())
    
    def get_world(self) -> World:
        """Obtenir le monde"""
        return self.world


def main():
    """Fonction principale"""
    # Initialiser la simulation
    simulation = Simulation()
    
    # Exécuter la simulation
    simulation.run()


if __name__ == "__main__":
    main()
