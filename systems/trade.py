"""
Classe TradeSystem - Système de commerce pour AI World
"""

import random
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict

from ..config import config
from ..utils.logger import Logger
from ..world.world import ResourceType
from ..agents.ai_agent import AIAgent


class TradeStatus(Enum):
    """Statuts des échanges"""
    PENDING = auto()    # En attente
    ACCEPTED = auto()   # Accepté
    REJECTED = auto()   # Refusé
    COMPLETED = auto()  # Complété
    CANCELLED = auto()  # Annulé


@dataclass
class TradeOffer:
    """Offre de commerce"""
    offer_id: str
    seller_id: str
    buyer_id: Optional[str] = None
    
    # Ce que le vendeur offre
    offered_items: Dict[ResourceType, float] = field(default_factory=dict)
    
    # Ce que le vendeur demande
    requested_items: Dict[ResourceType, float] = field(default_factory=dict)
    
    # Prix en ressources génériques (optionnel)
    price: float = 0.0
    
    # Statut
    status: TradeStatus = TradeStatus.PENDING
    
    # Timestamp
    timestamp: float = field(default_factory=lambda: time.time())
    
    # Position de rencontre (optionnelle)
    meeting_position: Optional[Any] = None  # Vector2
    
    def __post_init__(self):
        import time
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = time.time()
    
    def get_value(self, resource_values: Dict[ResourceType, float]) -> float:
        """Calculer la valeur de l'offre"""
        value = 0.0
        for resource_type, amount in self.offered_items.items():
            value += amount * resource_values.get(resource_type, 1.0)
        return value
    
    def get_requested_value(self, resource_values: Dict[ResourceType, float]) -> float:
        """Calculer la valeur demandée"""
        value = 0.0
        for resource_type, amount in self.requested_items.items():
            value += amount * resource_values.get(resource_type, 1.0)
        return value
    
    def is_fair(self, resource_values: Dict[ResourceType, float], 
                fairness_threshold: float = 0.9) -> bool:
        """Vérifier si l'offre est équitable"""
        offered_value = self.get_value(resource_values)
        requested_value = self.get_requested_value(resource_values)
        
        if requested_value == 0:
            return True
        
        ratio = offered_value / requested_value
        return fairness_threshold <= ratio <= 1 / fairness_threshold


@dataclass
class Market:
    """Représente un marché"""
    market_id: str
    name: str
    position: Any  # Vector2
    owner_id: Optional[str] = None
    group_id: Optional[str] = None
    
    # Offres disponibles
    offers: List[TradeOffer] = field(default_factory=list)
    
    # Historique des échanges
    trade_history: List[TradeOffer] = field(default_factory=list)
    
    # Valeurs des ressources (prix du marché)
    resource_values: Dict[ResourceType, float] = field(default_factory=lambda: {
        rt: 1.0 for rt in ResourceType
    })
    
    # Taxe
    tax_rate: float = 0.05
    
    def add_offer(self, offer: TradeOffer) -> bool:
        """Ajouter une offre au marché"""
        self.offers.append(offer)
        return True
    
    def remove_offer(self, offer_id: str) -> bool:
        """Retirer une offre"""
        for i, offer in enumerate(self.offers):
            if offer.offer_id == offer_id:
                del self.offers[i]
                return True
        return False
    
    def find_offers(self, buyer_id: str, resource_type: ResourceType = None,
                    max_price: float = None) -> List[TradeOffer]:
        """Trouver des offres correspondantes"""
        matching = []
        
        for offer in self.offers:
            if offer.seller_id == buyer_id:
                continue  # On ne peut pas acheter de soi-même
            
            if offer.status != TradeStatus.PENDING:
                continue
            
            if resource_type:
                # Vérifier si l'offre contient la ressource
                if resource_type not in offer.offered_items:
                    continue
            
            if max_price:
                offer_value = offer.get_value(self.resource_values)
                if offer_value > max_price:
                    continue
            
            matching.append(offer)
        
        return matching
    
    def accept_offer(self, offer_id: str, buyer: AIAgent) -> bool:
        """Accepter une offre"""
        for offer in self.offers:
            if offer.offer_id == offer_id:
                # Vérifier si le buyer a les ressources demandées
                for resource_type, amount in offer.requested_items.items():
                    if buyer.inventory.get(resource_type, 0) < amount:
                        return False
                
                # Mettre à jour l'offre
                offer.buyer_id = buyer.agent_id
                offer.status = TradeStatus.ACCEPTED
                
                # Exécuter l'échange
                self._execute_trade(offer, buyer)
                
                return True
        
        return False
    
    def _execute_trade(self, offer: TradeOffer, buyer: AIAgent):
        """Exécuter un échange"""
        # Trouver le vendeur
        seller = self._find_agent(offer.seller_id)
        if not seller:
            offer.status = TradeStatus.CANCELLED
            return
        
        # Transférer les ressources
        for resource_type, amount in offer.offered_items.items():
            if seller.inventory.get(resource_type, 0) >= amount:
                seller.inventory[resource_type] -= amount
                buyer.inventory[resource_type] = buyer.inventory.get(resource_type, 0) + amount
        
        for resource_type, amount in offer.requested_items.items():
            if buyer.inventory.get(resource_type, 0) >= amount:
                buyer.inventory[resource_type] -= amount
                seller.inventory[resource_type] = seller.inventory.get(resource_type, 0) + amount
        
        # Appliquer la taxe
        if self.owner_id and self.owner_id != offer.seller_id:
            tax = offer.get_value(self.resource_values) * self.tax_rate
            # Transférer la taxe au propriétaire du marché
            # (implémentation simplifiée)
        
        # Mettre à jour l'historique
        offer.status = TradeStatus.COMPLETED
        self.trade_history.append(offer)
        
        # Mettre à jour les valeurs du marché (apprentissage)
        self._update_resource_values(offer)
    
    def _find_agent(self, agent_id: str) -> Optional[AIAgent]:
        """Trouver un agent (à implémenter dans la simulation)"""
        # Dans une implémentation complète, on chercherait dans la liste des agents
        return None
    
    def _update_resource_values(self, trade: TradeOffer):
        """Mettre à jour les valeurs des ressources en fonction des échanges"""
        # Algorithme simplifié d'apprentissage
        # En réalité, on utiliserait un système plus sophistiqué
        pass


class TradeSystem:
    """
    Système de commerce pour AI World.
    Gère les échanges entre agents et les marchés.
    """
    
    def __init__(self):
        """Initialiser le système de commerce"""
        self.logger = Logger("TradeSystem")
        
        # Marchés
        self.markets: Dict[str, Market] = {}
        self.market_counter = 0
        
        # Offres directes (sans marché)
        self.direct_offers: Dict[str, TradeOffer] = {}
        
        # Historique des échanges
        self.trade_history: List[TradeOffer] = []
        
        # Statistiques
        self.stats = {
            "trades_completed": 0,
            "trades_pending": 0,
            "trades_rejected": 0,
            "total_value": 0.0
        }
        
        # Valeurs par défaut des ressources
        self.default_resource_values = {
            ResourceType.FOOD: 1.0,
            ResourceType.WOOD: 1.2,
            ResourceType.STONE: 1.5,
            ResourceType.METAL: 2.0,
            ResourceType.WATER: 0.5,
            ResourceType.GOLD: 5.0
        }
    
    def create_market(self, name: str, position, owner_id: str = None,
                      group_id: str = None) -> Market:
        """Créer un nouveau marché"""
        market_id = f"market_{self.market_counter}"
        self.market_counter += 1
        
        market = Market(
            market_id=market_id,
            name=name,
            position=position,
            owner_id=owner_id,
            group_id=group_id,
            resource_values=self.default_resource_values.copy()
        )
        
        self.markets[market_id] = market
        
        self.logger.info(f"Marché créé: {name} à {position}")
        
        return market
    
    def create_offer(self, seller: AIAgent, offered_items: Dict[ResourceType, float],
                     requested_items: Dict[ResourceType, float] = None,
                     price: float = 0.0, meeting_position: Any = None) -> TradeOffer:
        """Créer une nouvelle offre"""
        offer_id = f"offer_{len(self.direct_offers)}"
        
        offer = TradeOffer(
            offer_id=offer_id,
            seller_id=seller.agent_id,
            offered_items=offered_items.copy(),
            requested_items=requested_items or {},
            price=price,
            meeting_position=meeting_position
        )
        
        self.direct_offers[offer_id] = offer
        
        # Statistiques
        self.stats["trades_pending"] += 1
        
        self.logger.debug(f"Offre créée: {seller.name} offre {offered_items}")
        
        return offer
    
    def create_market_offer(self, seller: AIAgent, market_id: str,
                            offered_items: Dict[ResourceType, float],
                            requested_items: Dict[ResourceType, float] = None,
                            price: float = 0.0) -> Optional[TradeOffer]:
        """Créer une offre sur un marché"""
        if market_id not in self.markets:
            return None
        
        market = self.markets[market_id]
        
        offer = self.create_offer(
            seller, offered_items, requested_items, price
        )
        
        market.add_offer(offer)
        
        return offer
    
    def find_offers(self, buyer: AIAgent, resource_type: ResourceType = None,
                    max_price: float = None, market_id: str = None) -> List[TradeOffer]:
        """Trouver des offres correspondantes"""
        offers = []
        
        if market_id:
            # Chercher sur un marché spécifique
            if market_id in self.markets:
                offers.extend(self.markets[market_id].find_offers(
                    buyer.agent_id, resource_type, max_price
                ))
        else:
            # Chercher sur tous les marchés
            for market in self.markets.values():
                offers.extend(market.find_offers(
                    buyer.agent_id, resource_type, max_price
                ))
            
            # Chercher les offres directes
            for offer in self.direct_offers.values():
                if offer.seller_id != buyer.agent_id and offer.status == TradeStatus.PENDING:
                    if resource_type:
                        if resource_type in offer.offered_items:
                            offers.append(offer)
                    else:
                        offers.append(offer)
        
        return offers
    
    def accept_offer(self, offer_id: str, buyer: AIAgent, 
                     market_id: str = None) -> bool:
        """Accepter une offre"""
        # Chercher l'offre
        offer = None
        
        if market_id and market_id in self.markets:
            for o in self.markets[market_id].offers:
                if o.offer_id == offer_id:
                    offer = o
                    break
        else:
            offer = self.direct_offers.get(offer_id)
        
        if not offer:
            return False
        
        # Vérifier si le buyer a les ressources demandées
        for resource_type, amount in offer.requested_items.items():
            if buyer.inventory.get(resource_type, 0) < amount:
                self.logger.warning(f"{buyer.name} n'a pas assez de ressources pour l'offre {offer_id}")
                return False
        
        # Exécuter l'échange
        if market_id:
            self.markets[market_id]._execute_trade(offer, buyer)
        else:
            self._execute_direct_trade(offer, buyer)
        
        # Mettre à jour les statistiques
        self.stats["trades_pending"] -= 1
        self.stats["trades_completed"] += 1
        
        # Mettre à jour l'historique
        self.trade_history.append(offer)
        
        self.logger.info(f"Échange complété: {offer.seller_id} <-> {buyer.agent_id}")
        
        return True
    
    def _execute_direct_trade(self, offer: TradeOffer, buyer: AIAgent):
        """Exécuter un échange direct"""
        # Trouver le vendeur
        seller = self._find_agent(offer.seller_id)
        if not seller:
            offer.status = TradeStatus.CANCELLED
            return
        
        # Transférer les ressources
        for resource_type, amount in offer.offered_items.items():
            if seller.inventory.get(resource_type, 0) >= amount:
                seller.inventory[resource_type] -= amount
                buyer.inventory[resource_type] = buyer.inventory.get(resource_type, 0) + amount
        
        for resource_type, amount in offer.requested_items.items():
            if buyer.inventory.get(resource_type, 0) >= amount:
                buyer.inventory[resource_type] -= amount
                seller.inventory[resource_type] = seller.inventory.get(resource_type, 0) + amount
        
        # Mettre à jour le statut
        offer.status = TradeStatus.COMPLETED
        
        # Mettre à jour les statistiques
        trade_value = offer.get_value(self.default_resource_values)
        self.stats["total_value"] += trade_value
        
        # Notifier les agents
        seller.stats.trades_completed += 1
        buyer.stats.trades_completed += 1
    
    def _find_agent(self, agent_id: str) -> Optional[AIAgent]:
        """Trouver un agent (à implémenter dans la simulation)"""
        return None
    
    def reject_offer(self, offer_id: str, buyer: AIAgent = None) -> bool:
        """Refuser une offre"""
        # Chercher l'offre
        offer = self.direct_offers.get(offer_id)
        if not offer:
            for market in self.markets.values():
                for o in market.offers:
                    if o.offer_id == offer_id:
                        offer = o
                        break
        
        if not offer:
            return False
        
        offer.status = TradeStatus.REJECTED
        
        # Statistiques
        self.stats["trades_pending"] -= 1
        self.stats["trades_rejected"] += 1
        
        return True
    
    def cancel_offer(self, offer_id: str, seller: AIAgent) -> bool:
        """Annuler une offre"""
        # Chercher l'offre
        offer = self.direct_offers.get(offer_id)
        if not offer:
            for market in self.markets.values():
                for o in market.offers:
                    if o.offer_id == offer_id:
                        offer = o
                        break
        
        if not offer or offer.seller_id != seller.agent_id:
            return False
        
        offer.status = TradeStatus.CANCELLED
        
        # Statistiques
        self.stats["trades_pending"] -= 1
        
        return True
    
    def get_market(self, market_id: str) -> Optional[Market]:
        """Obtenir un marché"""
        return self.markets.get(market_id)
    
    def get_offers_by_seller(self, seller_id: str) -> List[TradeOffer]:
        """Obtenir les offres d'un vendeur"""
        offers = []
        
        # Offres directes
        for offer in self.direct_offers.values():
            if offer.seller_id == seller_id:
                offers.append(offer)
        
        # Offres sur les marchés
        for market in self.markets.values():
            for offer in market.offers:
                if offer.seller_id == seller_id:
                    offers.append(offer)
        
        return offers
    
    def get_trade_history(self, agent_id: str = None, limit: int = 100) -> List[TradeOffer]:
        """Obtenir l'historique des échanges"""
        if agent_id:
            return [
                t for t in self.trade_history
                if t.seller_id == agent_id or t.buyer_id == agent_id
            ][-limit:]
        return self.trade_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du système"""
        return {
            **self.stats,
            "markets": len(self.markets),
            "direct_offers": len(self.direct_offers),
            "market_offers": sum(len(m.offers) for m in self.markets.values())
        }
    
    def clear(self):
        """Effacer toutes les offres et marchés"""
        self.markets.clear()
        self.direct_offers.clear()
        self.trade_history.clear()
        self.stats = {
            "trades_completed": 0,
            "trades_pending": 0,
            "trades_rejected": 0,
            "total_value": 0.0
        }
    
    def suggest_trade(self, agent: AIAgent) -> Optional[TradeOffer]:
        """Suggérer un échange basé sur les besoins de l'agent"""
        # Analyser les besoins de l'agent
        needs = agent.needs.get_motivation_vector()
        
        # Trouver ce dont l'agent a besoin
        most_urgent_need = max(needs.items(), key=lambda x: x[1])
        
        # Mapper les besoins aux ressources
        need_to_resource = {
            NeedType.ENERGY: ResourceType.FOOD,
            NeedType.HEALTH: ResourceType.FOOD,
            NeedType.CREATION: ResourceType.WOOD,
            NeedType.SAFETY: ResourceType.STONE
        }
        
        needed_resource = need_to_resource.get(most_urgent_need[0])
        
        if not needed_resource:
            return None
        
        # Trouver ce que l'agent a en excès
        excess_resources = []
        for resource_type, amount in agent.inventory.items():
            if amount > 20:  # Seuil arbitraire
                excess_resources.append(resource_type)
        
        if not excess_resources:
            return None
        
        # Créer une offre
        offered_resource = random.choice(excess_resources)
        offered_amount = min(10, agent.inventory[offered_resource])
        
        offer = self.create_offer(
            seller=agent,
            offered_items={offered_resource: offered_amount},
            requested_items={needed_resource: offered_amount * 0.8}  # Prix légèrement inférieur
        )
        
        return offer
