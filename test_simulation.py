"""
Test de la simulation AI World
"""

import sys
import time
from typing import List

# Ajouter le chemin pour les imports
sys.path.insert(0, '/workspace')

from ai_world.config import config, AIType
from ai_world.world.world import World, ResourceType, TerrainType
from ai_world.agents.ai_agent import AIAgent, AgentState, AgentAction
from ai_world.agents.needs import NeedType
from ai_world.systems.communication import CommunicationSystem, Message, MessageType
from ai_world.systems.social import SocialSystem, Group, GroupType
from ai_world.systems.construction import ConstructionSystem, StructureType
from ai_world.systems.trade import TradeSystem
from ai_world.systems.combat import CombatSystem
from ai_world.systems.knowledge import KnowledgeSystem
from ai_world.systems.reproduction import ReproductionSystem
from ai_world.utils.vector import Vector2
from ai_world.utils.logger import Logger
from ai_world.utils.history import history_manager


def test_world():
    """Tester le monde"""
    print("Test du monde...")
    
    world = World(width=1000, height=800)
    
    # Vérifier la taille du monde
    assert world.width == 1000
    assert world.height == 800
    
    # Vérifier les ressources
    assert len(world.resources) > 0
    
    # Vérifier les cellules
    cell = world.get_cell_at(Vector2(50, 50))
    assert cell is not None
    
    # Vérifier la position valide
    assert world.is_position_valid(Vector2(100, 100))
    
    # Vérifier la position de spawn
    spawn_pos = world.get_random_spawn_position()
    assert spawn_pos is not None
    
    print("✓ Monde: OK")


def test_agents():
    """Tester les agents"""
    print("Test des agents...")
    
    world = World(width=1000, height=800)
    
    # Créer un agent
    agent = AIAgent(world=world, name="TestAgent")
    
    # Vérifier les propriétés de base
    assert agent.agent_id is not None
    assert agent.name == "TestAgent"
    assert agent.health == config.agent.initial_health
    assert agent.state == AgentState.IDLE
    
    # Vérifier la personnalité
    assert agent.personality is not None
    traits = agent.personality.get_all_traits()
    assert len(traits) > 0
    
    # Vérifier les besoins
    assert agent.needs is not None
    energy = agent.needs.get_need(NeedType.ENERGY)
    assert energy.current == config.agent.initial_energy
    
    # Vérifier les objectifs
    assert agent.goals is not None
    active_goal = agent.goals.get_active_goal()
    # Peut être None si aucun objectif actif
    
    # Vérifier la mémoire
    assert agent.memory is not None
    
    # Vérifier le déplacement
    target = Vector2(200, 200)
    agent.target_position = target
    agent.update(0.1)
    
    print("✓ Agents: OK")


def test_systems():
    """Tester les systèmes"""
    print("Test des systèmes...")
    
    world = World(width=1000, height=800)
    
    # Système de communication
    comm_system = CommunicationSystem()
    agent1 = AIAgent(world=world, name="Agent1")
    agent2 = AIAgent(world=world, name="Agent2")
    
    comm_system.register_agent(agent1.agent_id)
    comm_system.register_agent(agent2.agent_id)
    
    # Envoyer un message
    message = comm_system.send_message(
        sender=agent1,
        content="Hello!"
    )
    assert message is not None
    
    # Système social
    social_system = SocialSystem(comm_system)
    group = social_system.create_group(agent1, "TestGroup")
    assert group is not None
    assert social_system.join_group(agent2, group.group_id)
    
    # Système de construction
    constr_system = ConstructionSystem(world)
    project = constr_system.create_project(
        owner=agent1,
        structure_type=StructureType.HOUSE,
        position=Vector2(300, 300)
    )
    assert project is not None
    
    # Système de commerce
    trade_system = TradeSystem()
    offer = trade_system.create_offer(
        seller=agent1,
        offered_items={ResourceType.FOOD: 10}
    )
    assert offer is not None
    
    # Système de combat
    combat_system = CombatSystem()
    combat = combat_system.start_combat(agent1, agent2)
    assert combat is not None
    
    # Système de connaissance
    knowledge_system = KnowledgeSystem()
    knowledge = knowledge_system.create_knowledge(
        creator=agent1,
        topic="Test",
        content="Ceci est un test"
    )
    assert knowledge is not None
    
    # Système de reproduction
    reprod_system = ReproductionSystem(world)
    # Ne peut pas tester la reproduction sans deux agents prêts
    
    print("✓ Systèmes: OK")


def test_vector():
    """Tester le vecteur 2D"""
    print("Test du vecteur 2D...")
    
    v1 = Vector2(10, 20)
    v2 = Vector2(5, 10)
    
    # Addition
    v3 = v1 + v2
    assert v3.x == 15 and v3.y == 30
    
    # Soustraction
    v4 = v1 - v2
    assert v4.x == 5 and v4.y == 10
    
    # Multiplication
    v5 = v1 * 2
    assert v5.x == 20 and v5.y == 40
    
    # Division
    v6 = v1 / 2
    assert v6.x == 5 and v6.y == 10
    
    # Distance
    dist = v1.distance_to(v2)
    assert abs(dist - 11.18) < 0.1  # sqrt(5^2 + 10^2) ≈ 11.18
    
    # Longueur
    length = v1.length()
    assert abs(length - 22.36) < 0.1  # sqrt(10^2 + 20^2) ≈ 22.36
    
    print("✓ Vecteur 2D: OK")


def test_history():
    """Tester l'historique"""
    print("Test de l'historique...")
    
    history_manager.clear()
    
    # Ajouter des entrées
    history_manager.add_entry(
        "test_event",
        entity_id="agent1",
        data={"value": 42},
        simulation_time=0
    )
    
    history_manager.add_entry(
        "test_event2",
        entity_id="agent2",
        data={"value": 84},
        simulation_time=1
    )
    
    # Vérifier les entrées
    entries = history_manager.get_entries()
    assert len(entries) == 2
    
    # Vérifier par entité
    agent1_entries = history_manager.get_entries_by_entity("agent1")
    assert len(agent1_entries) == 1
    
    # Vérifier par type
    test_entries = history_manager.get_entries_by_type("test_event")
    assert len(test_entries) == 1
    
    print("✓ Historique: OK")


def test_logger():
    """Tester le logger"""
    print("Test du logger...")
    
    logger = Logger("TestLogger")
    
    # Tester les différents niveaux
    logger.debug("Message de debug")
    logger.info("Message d'information")
    logger.warning("Message d'avertissement")
    logger.error("Message d'erreur")
    logger.critical("Message critique")
    
    # Vérifier le buffer
    buffer = logger.get_buffer()
    assert len(buffer) > 0
    
    print("✓ Logger: OK")


def test_all():
    """Exécuter tous les tests"""
    print("\n=== Début des tests AI World ===\n")
    
    try:
        test_vector()
        test_world()
        test_agents()
        test_systems()
        test_history()
        test_logger()
        
        print("\n=== Tous les tests ont réussi ! ===\n")
        return True
    except Exception as e:
        print(f"\n❌ Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Désactiver l'affichage Pygame pour les tests
    import os
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    
    success = test_all()
    sys.exit(0 if success else 1)
