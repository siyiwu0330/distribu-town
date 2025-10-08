"""
公共数据模型
定义系统中所有实体的数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import json


class Occupation(Enum):
    """职业枚举"""
    CARPENTER = "carpenter"  # 木工
    FARMER = "farmer"        # 农夫
    CHEF = "chef"            # 厨师
    MERCHANT = "merchant"    # 商人（系统NPC）


class Gender(Enum):
    """性别枚举"""
    MALE = "male"
    FEMALE = "female"


class TimeOfDay(Enum):
    """时段枚举"""
    MORNING = "morning"
    NOON = "noon"
    EVENING = "evening"


class ItemType(Enum):
    """物品类型"""
    WOOD = "wood"          # 木材
    SEED = "seed"          # 种子
    WHEAT = "wheat"        # 小麦
    BREAD = "bread"        # 面包
    HOUSE = "house"        # 住房
    TEMP_ROOM = "temp_room"  # 临时房间券


@dataclass
class Inventory:
    """库存系统"""
    money: int = 100  # 初始货币
    items: Dict[str, int] = field(default_factory=dict)
    
    def add_item(self, item: str, quantity: int = 1):
        """添加物品"""
        if item not in self.items:
            self.items[item] = 0
        self.items[item] += quantity
    
    def remove_item(self, item: str, quantity: int = 1) -> bool:
        """移除物品，返回是否成功"""
        if item not in self.items or self.items[item] < quantity:
            return False
        self.items[item] -= quantity
        if self.items[item] == 0:
            del self.items[item]
        return True
    
    def has_item(self, item: str, quantity: int = 1) -> bool:
        """检查是否拥有足够的物品"""
        return item in self.items and self.items[item] >= quantity
    
    def add_money(self, amount: int):
        """增加货币"""
        self.money += amount
    
    def remove_money(self, amount: int) -> bool:
        """减少货币，返回是否成功"""
        if self.money < amount:
            return False
        self.money -= amount
        return True
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "money": self.money,
            "items": self.items
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Inventory':
        """从字典创建"""
        return cls(
            money=data.get("money", 100),
            items=data.get("items", {})
        )


@dataclass
class Villager:
    """村民数据模型"""
    name: str
    occupation: Occupation
    gender: Gender
    personality: str
    stamina: int = 100  # 体力
    max_stamina: int = 100
    inventory: Inventory = field(default_factory=Inventory)
    has_submitted_action: bool = False  # 当前时段是否已提交行动
    has_slept: bool = False  # 当天是否已睡眠
    
    def consume_stamina(self, amount: int) -> bool:
        """消耗体力"""
        if self.stamina < amount:
            return False
        self.stamina -= amount
        return True
    
    def restore_stamina(self, amount: int):
        """恢复体力"""
        self.stamina = min(self.stamina + amount, self.max_stamina)
    
    def reset_time_period(self):
        """重置时段状态（每次时间推进时调用）"""
        self.has_submitted_action = False
    
    def reset_daily(self):
        """每日重置"""
        self.has_submitted_action = False
        self.has_slept = False
        # 饥饿扣除体力
        self.stamina = max(0, self.stamina - 10)
        # 每日结算消耗临时房间券
        if self.inventory.has_item("temp_room", 1):
            self.inventory.remove_item("temp_room", 1)
    
    def eat_bread(self) -> bool:
        """吃面包恢复体力"""
        if not self.inventory.has_item("bread", 1):
            return False
        self.inventory.remove_item("bread", 1)
        self.restore_stamina(30)  # 恢复30点体力
        return True
    
    def to_dict(self) -> dict:
        """转换为字典"""
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
        """从字典创建"""
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
    """生产配方"""
    occupation: Occupation
    input_items: Dict[str, int]  # 输入物品 {item_type: quantity}
    output_item: str
    output_quantity: int
    stamina_cost: int
    
    def can_produce(self, inventory: Inventory, stamina: int) -> bool:
        """检查是否可以生产"""
        if stamina < self.stamina_cost:
            return False
        for item, quantity in self.input_items.items():
            if not inventory.has_item(item, quantity):
                return False
        return True


# 生产配方定义
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


# 商人价格表
MERCHANT_PRICES = {
    # 商人出售的价格（村民购买）- 基于体力=收益的量化标准
    "buy": {
        # 原材料 - 基于生产成本定价
        "seed": 5,         # 种子 (基础成本)
        "wheat": 10,       # 小麦 (收购价5 + 100%溢价)
        "wood": 15,        # 木材 (收购价10 + 50%溢价)
        
        # 产物 - 基于生产成本定价
        "bread": 90,       # 面包 (收购价45 + 100%溢价)
        "house": 260,      # 住房 (收购价130 + 100%溢价)
        
        # 特殊物品
        "temp_room": 15,  # 临时房间券 (合理定价)
    },
    # 商人收购的价格（村民出售）- 基于体力=收益的量化标准
    "sell": {
        # 原材料 - 基于体力价值定价
        "seed": 5,        # 种子 (基础成本)
        "wheat": 5,       # 小麦 (农夫: 20体力/5个 = 4体力/个，定价5)
        "wood": 10,       # 木材 (假设: 20体力/2个 = 10体力/个)
        
        # 产物 - 基于体力价值定价
        "bread": 45,    # 面包 (厨师: 15体力 + 3×5小麦 = 30，定价45)
        "house": 130,     # 住房 (木工: 30体力 + 10×10木材 = 130，定价130)
    }
}


# 其他常量
SLEEP_STAMINA = 30      # 睡眠恢复体力
NO_SLEEP_PENALTY = 20   # 不睡眠额外消耗体力
DAILY_HUNGER = 10       # 每日饥饿扣除体力
BREAD_RESTORE = 30      # 吃面包恢复体力


@dataclass
class GameState:
    """游戏状态"""
    day: int = 1
    time_of_day: TimeOfDay = TimeOfDay.MORNING
    
    def advance_time(self):
        """推进时间"""
        if self.time_of_day == TimeOfDay.MORNING:
            self.time_of_day = TimeOfDay.NOON
        elif self.time_of_day == TimeOfDay.NOON:
            self.time_of_day = TimeOfDay.EVENING
        elif self.time_of_day == TimeOfDay.EVENING:
            self.time_of_day = TimeOfDay.MORNING
            self.day += 1
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "day": self.day,
            "time_of_day": self.time_of_day.value if isinstance(self.time_of_day, TimeOfDay) else self.time_of_day
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GameState':
        """从字典创建"""
        time_of_day = TimeOfDay(data["time_of_day"]) if isinstance(data["time_of_day"], str) else data["time_of_day"]
        return cls(
            day=data["day"],
            time_of_day=time_of_day
        )


def json_serialize(obj):
    """JSON序列化辅助函数"""
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

