"""
Common Data Models
Defines data structures for all entities in the system
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import json


class Occupation(Enum):
    """Occupation enumeration"""
    CARPENTER = "carpenter"  # Carpenter
    FARMER = "farmer"        # Farmer
    CHEF = "chef"            # Chef
    MERCHANT = "merchant"    # Merchant (system NPC)


class Gender(Enum):
    """Gender enumeration"""
    MALE = "male"
    FEMALE = "female"


class TimeOfDay(Enum):
    """Time period enumeration"""
    MORNING = "morning"
    NOON = "noon"
    EVENING = "evening"


class ItemType(Enum):
    """Item types"""
    WOOD = "wood"          # Wood
    SEED = "seed"          # Seed
    WHEAT = "wheat"        # Wheat
    BREAD = "bread"        # Bread
    HOUSE = "house"        # House
    TEMP_ROOM = "temp_room"  # Temporary room voucher


@dataclass
class Inventory:
    """Inventory system"""
    money: int = 200  # Initial currency (increased to 200 to ensure can buy raw materials)
    items: Dict[str, int] = field(default_factory=dict)
    
    def add_item(self, item: str, quantity: int = 1):
        """Add item"""
        if item not in self.items:
            self.items[item] = 0
        self.items[item] += quantity
    
    def remove_item(self, item: str, quantity: int = 1) -> bool:
        """Remove item, returns success status"""
        if item not in self.items or self.items[item] < quantity:
            return False
        self.items[item] -= quantity
        if self.items[item] == 0:
            del self.items[item]
        return True
    
    def has_item(self, item: str, quantity: int = 1) -> bool:
        """Check if has enough items"""
        return item in self.items and self.items[item] >= quantity
    
    def add_money(self, amount: int):
        """Add money"""
        self.money += amount
    
    def remove_money(self, amount: int) -> bool:
        """Remove money, returns success status"""
        if self.money < amount:
            return False
        self.money -= amount
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "money": self.money,
            "items": self.items
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Inventory':
        """Create from dictionary"""
        return cls(
            money=data.get("money", 100),
            items=data.get("items", {})
        )


@dataclass
class Villager:
    """Villager data model"""
    name: str
    occupation: Occupation
    gender: Gender
    personality: str
    stamina: int = 100  # Stamina
    max_stamina: int = 100
    inventory: Inventory = field(default_factory=Inventory)
    has_submitted_action: bool = False  # Has submitted action for current time period
    has_slept: bool = False  # Has slept today
    
    def consume_stamina(self, amount: int) -> bool:
        """Consume stamina"""
        if self.stamina < amount:
            return False
        self.stamina -= amount
        return True
    
    def restore_stamina(self, amount: int):
        """Restore stamina"""
        self.stamina = min(self.stamina + amount, self.max_stamina)
    
    def reset_time_period(self):
        """Reset time period state (called each time advancement)"""
        self.has_submitted_action = False
    
    def reset_daily(self):
        """Daily reset"""
        self.has_submitted_action = False
        self.has_slept = False
        # Hunger deduction
        self.stamina = max(0, self.stamina - 10)
        # Daily settlement consumes temporary room voucher
        if self.inventory.has_item("temp_room", 1):
            self.inventory.remove_item("temp_room", 1)
    
    def eat_bread(self) -> bool:
        """Eat bread to restore stamina"""
        if not self.inventory.has_item("bread", 1):
            return False
        self.inventory.remove_item("bread", 1)
        self.restore_stamina(30)  # Restore 30 stamina
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "occupation": self.occupation.value if isinstance(self.occupation, Occupation) else self.occupation,
            "gender": self.gender.value if isinstance(self.gender, Gender) else self.gender,
            "personality": self.personality,
            "stamina": self.stamina,
            "max_stamina": self.max_stamina,
            "inventory": self.inventory.to_dict(),
            "has_submitted_action": self.has_submitted_action,
            "has_slept": self.has_slept
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Villager':
        """Create from dictionary"""
        occupation = Occupation(data["occupation"]) if isinstance(data["occupation"], str) else data["occupation"]
        gender = Gender(data["gender"]) if isinstance(data["gender"], str) else data["gender"]
        
        villager = cls(
            name=data["name"],
            occupation=occupation,
            gender=gender,
            personality=data["personality"],
            stamina=data.get("stamina", 100),
            max_stamina=data.get("max_stamina", 100),
            inventory=Inventory.from_dict(data.get("inventory", {})),
            has_submitted_action=data.get("has_submitted_action", False),
            has_slept=data.get("has_slept", False)
        )
        return villager


@dataclass
class ProductionRecipe:
    """Production recipe"""
    occupation: Occupation
    input_items: Dict[str, int]  # Input items {item_type: quantity}
    output_item: str
    output_quantity: int
    stamina_cost: int
    
    def can_produce(self, inventory: Inventory, stamina: int) -> bool:
        """Check if can produce"""
        if stamina < self.stamina_cost:
            return False
        for item, quantity in self.input_items.items():
            if not inventory.has_item(item, quantity):
                return False
        return True


# Production recipe definitions
PRODUCTION_RECIPES = {
    Occupation.CARPENTER: ProductionRecipe(
        occupation=Occupation.CARPENTER,
        input_items={"wood": 10},
        output_item="house",
        output_quantity=1,
        stamina_cost=30
    ),
    Occupation.FARMER: ProductionRecipe(
        occupation=Occupation.FARMER,
        input_items={"seed": 1},
        output_item="wheat",
        output_quantity=5,
        stamina_cost=20
    ),
    Occupation.CHEF: ProductionRecipe(
        occupation=Occupation.CHEF,
        input_items={"wheat": 3},
        output_item="bread",
        output_quantity=2,
        stamina_cost=15
    )
}


# Merchant price table
MERCHANT_PRICES = {
    # Merchant selling prices (villagers buying) - Based on stamina=income quantitative standard
    "buy": {
        # Raw materials - Priced based on production cost
        "seed": 5,         # Seed (base cost)
        "wheat": 10,       # Wheat (purchase price 5 + 100% markup)
        "wood": 10,        # Wood (purchase price 5 + 100% markup)
        
        # Products - Priced based on production cost
        "bread": 45,       # Bread (total cost 22.5 + 100% markup)
        "house": 260,      # House (purchase price 130 + 100% markup)
        
        # Special items
        "temp_room": 15,  # Temporary room voucher (reasonable pricing)
    },
    # Merchant buying prices (villagers selling) - Based on stamina=income quantitative standard
    "sell": {
        # Raw materials - Priced based on stamina value
        "seed": 5,        # Seed (base cost)
        "wheat": 5,       # Wheat (farmer: 20 stamina/5 items = 4 stamina/item, priced 5)
        "wood": 5,       # Wood (assumed: 20 stamina/2 items = 10 stamina/item)
        
        # Products - Priced based on stamina value
        "bread": 22.5,     # Bread (chef: 15 stamina + 3×10 wheat = 45, 2 breads, each 22.5)
        "house": 130,     # House (carpenter: 30 stamina + 10×15 wood = 180, priced 180)
    }
}


# Other constants
SLEEP_STAMINA = 30      # Stamina restored by sleep
NO_SLEEP_PENALTY = 20   # Extra stamina cost for not sleeping
DAILY_HUNGER = 10       # Daily hunger stamina deduction
BREAD_RESTORE = 60      # Stamina restored by eating bread


@dataclass
class GameState:
    """Game state"""
    day: int = 1
    time_of_day: TimeOfDay = TimeOfDay.MORNING
    
    def advance_time(self):
        """Advance time"""
        if self.time_of_day == TimeOfDay.MORNING:
            self.time_of_day = TimeOfDay.NOON
        elif self.time_of_day == TimeOfDay.NOON:
            self.time_of_day = TimeOfDay.EVENING
        elif self.time_of_day == TimeOfDay.EVENING:
            self.time_of_day = TimeOfDay.MORNING
            self.day += 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "day": self.day,
            "time_of_day": self.time_of_day.value if isinstance(self.time_of_day, TimeOfDay) else self.time_of_day
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GameState':
        """Create from dictionary"""
        time_of_day = TimeOfDay(data["time_of_day"]) if isinstance(data["time_of_day"], str) else data["time_of_day"]
        return cls(
            day=data["day"],
            time_of_day=time_of_day
        )


def json_serialize(obj):
    """JSON serialization helper function"""
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
