from typing import Any
from thespian.actors import *
from messages import MessageType

ORDER_DISTANCE = 10
COURIER_PRICES = [10, 15]

# try uncommenting the line below
# COURIER_PRICES = [13.5, 15.12, 9, 12, 11]

class OrderActor(Actor):
    def __init__(self):
        super().__init__()
        self.__courier_prices = {}
        self.__distance = None
        
    def receiveMessage(self, msg: tuple[MessageType, Any], sender: ActorAddress):
        msg_type, msg_data = msg
        
        match msg_type:
            
            case MessageType.Address:
                if self.__distance is None:
                    raise Exception("My distance is None")
                self.log(f"Send to {msg_data} my distance")
                self.send(msg_data, (MessageType.Distance, self.__distance))
                
            case MessageType.Price:
                self.__courier_prices[sender.actorAddressString] = (msg_data, sender)
                self.log(f"Get the price {msg_data} from {sender}")
                
                if len(self.__courier_prices) == len(COURIER_PRICES):
                    chosen = self.choose_courier()
                    self.send(chosen, (MessageType.Accept, ''))
                    self.log(f"I choose {chosen}")
                    
            case MessageType.Distance:
                self.__distance = float(msg_data)
                self.log(f"My distance is {self.__distance}")
                
            case MessageType.Ok:
                self.log(f"Courier {sender} must grab me")
                
            case _:
                raise Exception("Wrong message type: {_}")
    
    def choose_courier(self):
        demanded_courier = min(self.__courier_prices.items(), key=lambda p: p[1][0])
        return demanded_courier[1][1]
    
    def log(self, data: str):
        print(f"Order: {data}")


class CourierActor(Actor): 
    def __init__(self):
        super().__init__()
        self.__price = None
        
    def receiveMessage(self, msg: tuple[MessageType, Any], sender: ActorAddress):
        msg_type, msg_data = msg
        
        match msg_type:
            
            case MessageType.Distance:
                if self.__price is None:
                    raise Exception("My price is None")
                price = self.__price * float(msg_data)
                self.log(f"I send my price for order: {price}")
                self.send(sender, (MessageType.Price, price))
                
            case MessageType.Accept:
                self.log(f"Im the chosen one!!! I send 'ok' to order")
                self.send(sender, (MessageType.Ok, ''))
            
            case MessageType.PricePerKm:
                self.__price = float(msg_data)
                self.log(f"My price per km is {self.__price}")
                
            case _:
                raise Exception("Wrong message type: {_}")
    
    def log(self, data: str):
        print(f"Courier {self.myAddress}: {data}")
        

def main():
    actor_system = ActorSystem()
    
    order = actor_system.createActor(OrderActor)
    actor_system.tell(order, (MessageType.Distance, ORDER_DISTANCE))
    
    couriers = []
    for courier_price in COURIER_PRICES:
        courier = actor_system.createActor(CourierActor)
        couriers.append(courier)
        actor_system.tell(courier, (MessageType.PricePerKm, courier_price))
        actor_system.tell(order, (MessageType.Address, courier))
    
        
    
if __name__ == "__main__":
    main()