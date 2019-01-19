import threading
import time


class UserInterface(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.buffer = []

    def run(self):
        """
        Which the user or client sees and works with.
        This method runs every time to see whether there are new messages or not.
        """

        print("here")
        while True:
            message = input("Write your command:\n")
            self.buffer.append(message)
            print(self.buffer)
