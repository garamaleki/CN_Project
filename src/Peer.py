import threading

from src.tools.Node import Node
from src.tools.simpletcp.tcpserver import TCPServer


class Stream:

    def __init__(self, ip, port):
        def callback(address, queue, data):
            """
            The callback function will run when a new data received from server_buffer.

            :param address: Source address.
            :param queue: Response queue.
            :param data: The data received from the socket.
            :return:
            """
            queue.put(bytes('ACK', 'utf8'))
            self._server_in_buf.append(data)

        """
        The Stream object constructor.

        Code design suggestion:
            1. Make a separate Thread for your TCPServer and start immediately.


        :param ip: 15 characters
        :param port: 5 characters
        """

        self.ip = Node.parse_ip(ip)
        self.port = Node.parse_port(port)
        self._server_in_buf = []
        self.nodes = []
        mode = ip
        if (ip == Node.parse_ip("0.0.0.0")):
            mode = "public"
        elif (ip == Node.parse_ip("127.0.0.1")):
            mode = "localhost"

        self.tcp_server = TCPServer(mode, port, callback, 5, 2048)
        receive_thread = threading.Thread(target=self.tcp_server.run)
        receive_thread.start()

    def get_server_address(self):
        """

        :return: Our TCPServer address
        :rtype: tuple
        """
        return (self.ip, self.port)

    def clear_in_buff(self):
        """
        Discard any data in TCPServer input buffer.

        :return:
        """
        self._server_in_buf.clear()

    def add_node(self, server_address, set_register_connection=False):
        """
        Will add new a node to our Stream.

        :param server_address: New node TCPServer address.
        :param set_register_connection: Shows that is this connection a register_connection or not.

        :type server_address: tuple
        :type set_register_connection: bool

        :return:
        """
        check = True
        for node in self.nodes:
            nip = node.get_server_address()[0]
            nport = node.get_server_address()[1]
            nregister = node.get_is_register()
            if nip == Node.parse_ip(server_address[0]) and nport == Node.parse_port(server_address[1]) and nregister == set_register_connection:
                check = False
        if check:
            self.nodes.append(Node(server_address, set_register_connection))

    def remove_node(self, node):
        """
        Remove the node from our Stream.

        Warnings:
            1. Close the node after deletion.

        :param node: The node we want to remove.
        :type node: Node

        :return:
        """
        self.nodes.remove(node)
        node.close()

    def get_node_by_server(self, ip, port):
        """

        Will find the node that has IP/Port address of input.

        Warnings:
            1. Before comparing the address parse it to a standard format with Node.parse_### functions.

        :param ip: input address IP
        :param port: input address Port

        :return: The node that input address.
        :rtype: Node
        """
        nip = Node.parse_ip(ip)
        nport = Node.parse_port(port)
        for node in self.nodes:
            if node.get_server_address()[0] == nip and node.get_server_address()[1] == nport:
                return node

    def add_message_to_out_buff(self, address, is_root, message):
        """
        In this function, we will add the message to the output buffer of the node that has the input address.
        Later we should use send_out_buf_messages to send these buffers into their sockets.

        :param address: Node address that we want to send the message
        :param message: Message we want to send

        Warnings:
            1. Check whether the node address is in our nodes or not.

        :return:
        """
        naddress = (Node.parse_ip(address[0]), Node.parse_port(address[1]))
        for node in self.nodes:
            if node.get_server_address() == naddress and node.get_is_register() == is_root:
                node.add_message_to_out_buff(message)

    def read_in_buf(self):
        """
        Only returns the input buffer of our TCPServer.

        :return: TCPServer input buffer.
        :rtype: list
        """
        return self._server_in_buf

    def send_messages_to_node(self, node):
        """
        Send buffered messages to the 'node'

        Warnings:
            1. Insert an exception handler here; Maybe the node socket you want to send the message has turned off and
            you need to remove this node from stream nodes.

        :param node:
        :type node Node

        :return:
        """
        try:
            node.send_message()
        except Exception:
            self.remove_node(node)

    def send_out_buf_messages(self, only_register=False):
        """
        In this function, we will send hole out buffers to their own clients.

        :return:
        """
        if only_register:
            for node in self.nodes:
                if (node.get_is_register()):
                    self.send_messages_to_node(node)
        else:
            for node in self.nodes:
                    self.send_messages_to_node(node)
