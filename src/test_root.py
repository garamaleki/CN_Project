from src.Peer import Peer
server = Peer("127.0.0.1", 6333, is_root=True)
server.run()