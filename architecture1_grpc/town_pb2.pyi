from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Status(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class Inventory(_message.Message):
    __slots__ = ("money", "items")
    class ItemsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    MONEY_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    money: int
    items: _containers.ScalarMap[str, int]
    def __init__(self, money: _Optional[int] = ..., items: _Optional[_Mapping[str, int]] = ...) -> None: ...

class VillagerInfo(_message.Message):
    __slots__ = ("name", "occupation", "gender", "personality", "stamina", "max_stamina", "inventory", "action_points", "has_slept")
    NAME_FIELD_NUMBER: _ClassVar[int]
    OCCUPATION_FIELD_NUMBER: _ClassVar[int]
    GENDER_FIELD_NUMBER: _ClassVar[int]
    PERSONALITY_FIELD_NUMBER: _ClassVar[int]
    STAMINA_FIELD_NUMBER: _ClassVar[int]
    MAX_STAMINA_FIELD_NUMBER: _ClassVar[int]
    INVENTORY_FIELD_NUMBER: _ClassVar[int]
    ACTION_POINTS_FIELD_NUMBER: _ClassVar[int]
    HAS_SLEPT_FIELD_NUMBER: _ClassVar[int]
    name: str
    occupation: str
    gender: str
    personality: str
    stamina: int
    max_stamina: int
    inventory: Inventory
    action_points: int
    has_slept: bool
    def __init__(self, name: _Optional[str] = ..., occupation: _Optional[str] = ..., gender: _Optional[str] = ..., personality: _Optional[str] = ..., stamina: _Optional[int] = ..., max_stamina: _Optional[int] = ..., inventory: _Optional[_Union[Inventory, _Mapping]] = ..., action_points: _Optional[int] = ..., has_slept: bool = ...) -> None: ...

class GameTime(_message.Message):
    __slots__ = ("day", "time_of_day")
    DAY_FIELD_NUMBER: _ClassVar[int]
    TIME_OF_DAY_FIELD_NUMBER: _ClassVar[int]
    day: int
    time_of_day: str
    def __init__(self, day: _Optional[int] = ..., time_of_day: _Optional[str] = ...) -> None: ...

class RegisterNodeRequest(_message.Message):
    __slots__ = ("node_id", "node_type", "address")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_TYPE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    node_type: str
    address: str
    def __init__(self, node_id: _Optional[str] = ..., node_type: _Optional[str] = ..., address: _Optional[str] = ...) -> None: ...

class TimeAdvanceNotification(_message.Message):
    __slots__ = ("new_time",)
    NEW_TIME_FIELD_NUMBER: _ClassVar[int]
    new_time: GameTime
    def __init__(self, new_time: _Optional[_Union[GameTime, _Mapping]] = ...) -> None: ...

class NodeList(_message.Message):
    __slots__ = ("nodes",)
    NODES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeInfo]
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeInfo, _Mapping]]] = ...) -> None: ...

class NodeInfo(_message.Message):
    __slots__ = ("node_id", "node_type", "address")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_TYPE_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    node_type: str
    address: str
    def __init__(self, node_id: _Optional[str] = ..., node_type: _Optional[str] = ..., address: _Optional[str] = ...) -> None: ...

class CreateVillagerRequest(_message.Message):
    __slots__ = ("name", "occupation", "gender", "personality")
    NAME_FIELD_NUMBER: _ClassVar[int]
    OCCUPATION_FIELD_NUMBER: _ClassVar[int]
    GENDER_FIELD_NUMBER: _ClassVar[int]
    PERSONALITY_FIELD_NUMBER: _ClassVar[int]
    name: str
    occupation: str
    gender: str
    personality: str
    def __init__(self, name: _Optional[str] = ..., occupation: _Optional[str] = ..., gender: _Optional[str] = ..., personality: _Optional[str] = ...) -> None: ...

class ProduceRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TradeRequest(_message.Message):
    __slots__ = ("target_node", "item", "quantity", "price")
    TARGET_NODE_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    target_node: str
    item: str
    quantity: int
    price: int
    def __init__(self, target_node: _Optional[str] = ..., item: _Optional[str] = ..., quantity: _Optional[int] = ..., price: _Optional[int] = ...) -> None: ...

class SleepRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TradeExecuteRequest(_message.Message):
    __slots__ = ("action", "item", "quantity", "money")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    MONEY_FIELD_NUMBER: _ClassVar[int]
    action: str
    item: str
    quantity: int
    money: int
    def __init__(self, action: _Optional[str] = ..., item: _Optional[str] = ..., quantity: _Optional[int] = ..., money: _Optional[int] = ...) -> None: ...

class BuyFromMerchantRequest(_message.Message):
    __slots__ = ("buyer_id", "item", "quantity")
    BUYER_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    buyer_id: str
    item: str
    quantity: int
    def __init__(self, buyer_id: _Optional[str] = ..., item: _Optional[str] = ..., quantity: _Optional[int] = ...) -> None: ...

class SellToMerchantRequest(_message.Message):
    __slots__ = ("seller_id", "item", "quantity")
    SELLER_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    seller_id: str
    item: str
    quantity: int
    def __init__(self, seller_id: _Optional[str] = ..., item: _Optional[str] = ..., quantity: _Optional[int] = ...) -> None: ...

class PriceInfo(_message.Message):
    __slots__ = ("item", "price")
    ITEM_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    item: str
    price: int
    def __init__(self, item: _Optional[str] = ..., price: _Optional[int] = ...) -> None: ...

class PriceList(_message.Message):
    __slots__ = ("buy_prices", "sell_prices")
    BUY_PRICES_FIELD_NUMBER: _ClassVar[int]
    SELL_PRICES_FIELD_NUMBER: _ClassVar[int]
    buy_prices: _containers.RepeatedCompositeFieldContainer[PriceInfo]
    sell_prices: _containers.RepeatedCompositeFieldContainer[PriceInfo]
    def __init__(self, buy_prices: _Optional[_Iterable[_Union[PriceInfo, _Mapping]]] = ..., sell_prices: _Optional[_Iterable[_Union[PriceInfo, _Mapping]]] = ...) -> None: ...

class CreateTradeRequest(_message.Message):
    __slots__ = ("initiator_id", "initiator_address", "target_id", "target_address", "offer_type", "item", "quantity", "price")
    INITIATOR_ID_FIELD_NUMBER: _ClassVar[int]
    INITIATOR_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    TARGET_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    OFFER_TYPE_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    initiator_id: str
    initiator_address: str
    target_id: str
    target_address: str
    offer_type: str
    item: str
    quantity: int
    price: int
    def __init__(self, initiator_id: _Optional[str] = ..., initiator_address: _Optional[str] = ..., target_id: _Optional[str] = ..., target_address: _Optional[str] = ..., offer_type: _Optional[str] = ..., item: _Optional[str] = ..., quantity: _Optional[int] = ..., price: _Optional[int] = ...) -> None: ...

class CreateTradeResponse(_message.Message):
    __slots__ = ("success", "message", "trade_id")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TRADE_ID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    trade_id: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., trade_id: _Optional[str] = ...) -> None: ...

class TradeInfo(_message.Message):
    __slots__ = ("trade_id", "initiator_id", "initiator_address", "target_id", "target_address", "offer_type", "item", "quantity", "price", "status", "initiator_confirmed", "target_confirmed")
    TRADE_ID_FIELD_NUMBER: _ClassVar[int]
    INITIATOR_ID_FIELD_NUMBER: _ClassVar[int]
    INITIATOR_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    TARGET_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    OFFER_TYPE_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    INITIATOR_CONFIRMED_FIELD_NUMBER: _ClassVar[int]
    TARGET_CONFIRMED_FIELD_NUMBER: _ClassVar[int]
    trade_id: str
    initiator_id: str
    initiator_address: str
    target_id: str
    target_address: str
    offer_type: str
    item: str
    quantity: int
    price: int
    status: str
    initiator_confirmed: bool
    target_confirmed: bool
    def __init__(self, trade_id: _Optional[str] = ..., initiator_id: _Optional[str] = ..., initiator_address: _Optional[str] = ..., target_id: _Optional[str] = ..., target_address: _Optional[str] = ..., offer_type: _Optional[str] = ..., item: _Optional[str] = ..., quantity: _Optional[int] = ..., price: _Optional[int] = ..., status: _Optional[str] = ..., initiator_confirmed: bool = ..., target_confirmed: bool = ...) -> None: ...

class ListTradesRequest(_message.Message):
    __slots__ = ("node_id", "type")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    type: str
    def __init__(self, node_id: _Optional[str] = ..., type: _Optional[str] = ...) -> None: ...

class ListTradesResponse(_message.Message):
    __slots__ = ("trades",)
    TRADES_FIELD_NUMBER: _ClassVar[int]
    trades: _containers.RepeatedCompositeFieldContainer[TradeInfo]
    def __init__(self, trades: _Optional[_Iterable[_Union[TradeInfo, _Mapping]]] = ...) -> None: ...

class AcceptTradeRequest(_message.Message):
    __slots__ = ("trade_id", "node_id")
    TRADE_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    trade_id: str
    node_id: str
    def __init__(self, trade_id: _Optional[str] = ..., node_id: _Optional[str] = ...) -> None: ...

class ConfirmTradeRequest(_message.Message):
    __slots__ = ("trade_id", "node_id")
    TRADE_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    trade_id: str
    node_id: str
    def __init__(self, trade_id: _Optional[str] = ..., node_id: _Optional[str] = ...) -> None: ...

class CancelTradeRequest(_message.Message):
    __slots__ = ("trade_id", "node_id")
    TRADE_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    trade_id: str
    node_id: str
    def __init__(self, trade_id: _Optional[str] = ..., node_id: _Optional[str] = ...) -> None: ...

class RejectTradeRequest(_message.Message):
    __slots__ = ("trade_id", "node_id")
    TRADE_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    trade_id: str
    node_id: str
    def __init__(self, trade_id: _Optional[str] = ..., node_id: _Optional[str] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ("message_id", "to", "content", "type", "timestamp", "is_read")
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    FROM_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    IS_READ_FIELD_NUMBER: _ClassVar[int]
    message_id: str
    to: str
    content: str
    type: str
    timestamp: int
    is_read: bool
    def __init__(self, message_id: _Optional[str] = ..., to: _Optional[str] = ..., content: _Optional[str] = ..., type: _Optional[str] = ..., timestamp: _Optional[int] = ..., is_read: bool = ..., **kwargs) -> None: ...

class SendMessageRequest(_message.Message):
    __slots__ = ("target", "content", "type")
    TARGET_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    target: str
    content: str
    type: str
    def __init__(self, target: _Optional[str] = ..., content: _Optional[str] = ..., type: _Optional[str] = ...) -> None: ...

class SendMessageResponse(_message.Message):
    __slots__ = ("success", "message", "message_id")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    message_id: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., message_id: _Optional[str] = ...) -> None: ...

class ReceiveMessageRequest(_message.Message):
    __slots__ = ("content", "type", "timestamp")
    FROM_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    content: str
    type: str
    timestamp: int
    def __init__(self, content: _Optional[str] = ..., type: _Optional[str] = ..., timestamp: _Optional[int] = ..., **kwargs) -> None: ...

class ReceiveMessageResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class GetMessagesRequest(_message.Message):
    __slots__ = ("node_id",)
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    def __init__(self, node_id: _Optional[str] = ...) -> None: ...

class GetMessagesResponse(_message.Message):
    __slots__ = ("messages",)
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    messages: _containers.RepeatedCompositeFieldContainer[Message]
    def __init__(self, messages: _Optional[_Iterable[_Union[Message, _Mapping]]] = ...) -> None: ...
