from src.Peer import Peer

if __name__ == "__main__":
    server = Peer("127.0.0.1", 6333, is_root=True)
    server.run()

    # Needs to be run in seprate files or use threading

    client = Peer("127.0.0.1", 5055, is_root=False,
                  root_address=("127.0.0.1", 6333))

    client.run()