from typing import Any
from thespian.actors import *
from messages import MessageType
import random

N_COURIERS = 5
COURIER_PRICES = [13.5, 15.12, 9, 12, 11]

class OrderActor(Actor):
    def __init__(self):
        super().__init__()
        self.courier_prices = {}
        self.distance = None
    
    def set_distance(self, distance_km: float):
        self.distance = distance_km
        
    def receiveMessage(self, msg: tuple[MessageType, Any], sender: ActorAddress):
        msg_type, msg_data = msg
        
        match msg_type:
            
            case MessageType.Address:
                self.send(msg[1], (MessageType.Greetings, "sdfsdf"))
            case MessageType.RussianGreetings:
                pass
            case _:
                raise Exception("Wrong message type: {_}")
    
    def log(self, data: str):
        print(f"Courier {self.myAddress}: {data}")
        

def main():
    actor_system = ActorSystem()
    
    order = actor_system.createActor(OrderActor)
    actor_system.tell(order, (MessageType.Distance, 10))
    
    couriers = []
    for i in range(N_COURIERS):
        courier = actor_system.createActor(CourierActor)
        couriers.append(courier)
        actor_system.tell(courier, (MessageType.PricePerKm, COURIER_PRICES[i]))
        actor_system.tell(order, (MessageType.Address, courier))
    
if __name__ == "__main__":
    main()