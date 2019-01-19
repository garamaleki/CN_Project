from src.Peer import Peer

client = Peer("127.0.0.1", 5053, is_root=False,
              root_address=("127.0.0.1", 6333))



client.run()