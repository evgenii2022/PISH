from enum import Enum

class MessageType(Enum):
    Address = 0
    Distance = 1
    Price = 2
    PricePerKm = 2
    Accept = 3
    Ok = 4
    