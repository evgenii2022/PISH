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
                if self.distance is None:
                    raise Exception("My distance is None")
                self.log(f"Send to {msg[1]} my distance")
                self.send(msg[1], (MessageType.Distance, self.distance))
                
            case MessageType.Price:
                self.courier_prices[sender.actorAddressString] = (msg_data, sender)
                self.log(f"Get the price {msg_data} from {sender}")
                
                if len(self.courier_prices) == N_COURIERS:
                    chosen = self.choose_courier()
                    self.send(chosen, (MessageType.Accept, ''))
                    self.log(f"I choose {chosen}")
                    
            case MessageType.Distance:
                self.distance = float(msg_data)
                self.log(f"My distance is {self.distance}")
                
            case MessageType.Ok:
                self.log(f"Courier {sender} must grab me")
                
            case _:
                raise Exception("Wrong message type: {_}")
    
    def choose_courier(self):
        demanded_courier = min(self.courier_prices.items(), key=lambda p: p[1][0])
        return demanded_courier[1][1]
    
    def log(self, data: str):
        print(f"Order: {data}")


class CourierActor(Actor): 
    def __init__(self):
        super().__init__()
        self.price = None
        
    def receiveMessage(self, msg: tuple[MessageType, Any], sender: ActorAddress):
        msg_type, msg_data = msg
        
        match msg_type:
            
            case MessageType.Distance:
                if self.price is None:
                    raise Exception("My price is None")
                price = self.price * float(msg_data)
                self.log(f"I send my price for order: {price}")
                self.send(sender, (MessageType.Price, price))
                
            case MessageType.Accept:
                self.log(f"Im the chosen one!!! I send 'ok' to order")
                self.send(sender, (MessageType.Ok, ''))
            
            case MessageType.PricePerKm:
                self.price = float(msg_data)
                self.log(f"My price per km is {self.price}")
                
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