from thespian.actors import *
from messages import MessageType


class SimplestActor(Actor):
    def receiveMessage(self, msg: tuple[str, str], sender: str):
        if not isinstance(msg, tuple) or len(msg) != 2:
            raise ValueError("Message must be tuple[str, str]")  
        print(f"The actor got '{msg}' from {sender}")
        msg_type = msg[0]
        match msg_type:
            case MessageType.Greetings:
                self.send(sender, (MessageType.RussianGreetings, "kkkkk"))
            case MessageType.Address:
                self.send(msg[1], (MessageType.Greetings, "sdfsdf"))
            case MessageType.RussianGreetings:
                pass
            case _:
                raise Exception("Wrong message type: {_}")                

def main():
    actor_system = ActorSystem()
    
    actor_address = actor_system.createActor(SimplestActor)
    actor_address2 = actor_system.createActor(SimplestActor)
    
    address_message = (MessageType.Address, actor_address)
    actor_system.tell(actor_address2, address_message)
    
    #result = actor_system.listen()
    
    #print(f"The actor system got a message: {result}")
    
    
if __name__ == "__main__":
    main()