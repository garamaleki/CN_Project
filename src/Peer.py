from src.Stream import Stream
from src.Packet import Packet, PacketFactory
from src.UserInterface import UserInterface
from src.tools.SemiNode import SemiNode
from src.tools.NetworkGraph import NetworkGraph, GraphNode
import time
import threading

"""
    Peer is our main object in this project.
    In this network Peers will connect together to make a tree graph.
    This network is not completely decentralised but will show you some real-world challenges in Peer to Peer networks.

"""

REUNION_DAEMON_INTERVAL = 1
MAX_REUNION_INTERVAL = 35


# When reunion failed for non-root peer, close all non-register nodes


class Peer:
    def __init__(self, server_ip, server_port, is_root=False, root_address=None):
        """
        The Peer object constructor.

        Code design suggestions:
            1. Initialise a Stream object for our Peer.
            2. Initialise a PacketFactory object.
            3. Initialise our UserInterface for interaction with user commandline.
            4. Initialise a Thread for handling reunion daemon.

        Warnings:
            1. For root Peer, we need a NetworkGraph object.
            2. In root Peer, start reunion daemon as soon as possible.
            3. In client Peer, we need to connect to the root of the network, Don't forget to set this connection
               as a register_connection.


        :param server_ip: Server IP address for this Peer that should be pass to Stream.
        :param server_port: Server Port address for this Peer that should be pass to Stream.
        :param is_root: Specify that is this Peer root or not.
        :param root_address: Root IP/Port address if we are a client.

        :type server_ip: str
        :type server_port: int
        :type is_root: bool
        :type root_address: tuple
        """

        self.ip = SemiNode.parse_ip(server_ip)
        self.port = SemiNode.parse_port(server_port)
        self.is_root = is_root
        self.packet_factory = PacketFactory()
        self.user_interface = UserInterface(str(server_ip) + " " + str(server_port))
        time.sleep(0.2)
        self.stream = Stream(server_ip, server_port)
        self.start_user_interface()
        self.reunion_daemon_thread = threading.Thread(target=self.run_reunion_daemon)
        self.parent_address = None
        self.neighbours_address = []

        if is_root:
            self.network_graph = NetworkGraph(GraphNode((SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port))))
            self.reunion_arrival_time_per_peer = {}
            self.reunion_daemon_thread.start()
        else:
            self.root_address = root_address
            self.reunion_send_time, self.reunion_arrival_time = None, time.time()
            self.is_waiting = False
            self.first_advertise = True

    def start_user_interface(self):
        """
        For starting UserInterface thread.

        :return:
        """
        self.user_interface.start()

    def handle_user_interface_buffer(self):
        """
        In every interval, we should parse user command that buffered from our UserInterface.
        All of the valid commands are listed below:
            1. Register:  With this command, the client send a Register Request packet to the root of the network.
            2. Advertise: Send an Advertise Request to the root of the network for finding first hope.
            3. SendMessage: The following string will be added to a new Message packet and broadcast through the network.

        Warnings:
            1. Ignore irregular commands from the user.
            2. Don't forget to clear our UserInterface buffer.
        :return:
        """

        while len(self.user_interface.buffer) > 0:

            message = self.user_interface.buffer.pop()

            if message == "Register" and not self.is_root:
                packet = self.packet_factory.new_register_packet("request", (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)), (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)))

                self.stream.add_node((self.root_address[0], self.root_address[1]), True)
                self.stream.add_message_to_out_buff((self.root_address[0], self.root_address[1]), True, packet.get_buf())
            elif message == "Advertise" and not self.is_root:
                packet = self.packet_factory.new_advertise_packet("request", (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)))

                self.stream.add_node((self.root_address[0], self.root_address[1]), True)

                self.stream.add_message_to_out_buff((self.root_address[0], self.root_address[1]), True, packet.get_buf())
            elif message[:11] == "SendMessage":
                message_body = message[11:]
                packet = self.packet_factory.new_message_packet(message_body, (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)))

                self.send_broadcast_packet(packet)

    def run(self):
        """
        The main loop of the program.

        Code design suggestions:
            1. Parse server in_buf of the stream.
            2. Handle all packets were received from our Stream server.
            3. Parse user_interface_buffer to make message packets.
            4. Send packets stored in nodes buffer of our Stream object.
            5. ** sleep the current thread for 2 seconds **

        Warnings:
            1. At first check reunion daemon condition; Maybe we have a problem in this time
               and so we should hold any actions until Reunion acceptance.
            2. In every situation checkout Advertise Response packets; even is Reunion in failure mode or not

        :return:
        """
        time.sleep(1)

        # TODO: Check reunion????
        while True:
            self.user_interface.add_log(self.stream.read_in_buf())
            stream_buf = self.stream.read_in_buf()
            for buf in stream_buf:  # Are there packets or do we need to parse them?
                self.handle_packet(PacketFactory.parse_buffer(buf))
            self.stream.clear_in_buff()

            self.handle_user_interface_buffer()
            self.stream.send_out_buf_messages()
            time.sleep(2)

    def run_reunion_daemon(self):
        """

        In this function, we will handle all Reunion actions.

        Code design suggestions:
            1. Check if we are the network root or not; The actions are identical.
            2. If it's the root Peer, in every interval check the latest Reunion packet arrival time from every node;
               If time is over for the node turn it off (Maybe you need to remove it from our NetworkGraph).
            3. If it's a non-root peer split the actions by considering whether we are waiting for Reunion Hello Back
               Packet or it's the time to send new Reunion Hello packet.

        Warnings:
            1. If we are the root of the network in the situation that we want to turn a node off, make sure that you will not
               advertise the nodes sub-tree in our GraphNode.
            2. If we are a non-root Peer, save the time when you have sent your last Reunion Hello packet; You need this
               time for checking whether the Reunion was failed or not.
            3. For choosing time intervals you should wait until Reunion Hello or Reunion Hello Back arrival,
               pay attention that our NetworkGraph depth will not be bigger than 8. (Do not forget main loop sleep time)
            4. Suppose that you are a non-root Peer and Reunion was failed, In this time you should make a new Advertise
               Request packet and send it through your register_connection to the root; Don't forget to send this packet
               here, because in the Reunion Failure mode our main loop will not work properly and everything will be got stock!

        :return:
        """

        while True:
            if self.is_root:

                for node in self.network_graph.nodes:
                    if node.address == (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)):
                        continue
                    if node.alive and self.reunion_arrival_time_per_peer[node.address] + MAX_REUNION_INTERVAL < time.time():

                        if self.reunion_arrival_time_per_peer[node.address]:
                            del self.reunion_arrival_time_per_peer[node.address]

                        if node.address in self.neighbours_address:
                            self.neighbours_address.remove(node.address)
                        self.network_graph.remove_node(node.address)

            else:

                if self.reunion_arrival_time + MAX_REUNION_INTERVAL < time.time() and self.is_waiting:
                    self.is_waiting = False
                    self.neighbours_address.clear()

            time.sleep(REUNION_DAEMON_INTERVAL)

    def send_broadcast_packet(self, broadcast_packet):
        """

        For setting broadcast packets buffer into Nodes out_buff.

        Warnings:
            1. Don't send Message packets through register_connections.

        :param broadcast_packet: The packet that should be broadcast through the network.
        :type broadcast_packet: Packet

        :return:
        """

        for neighbour_address in self.neighbours_address:

            self.stream.add_message_to_out_buff(neighbour_address, False, broadcast_packet.get_buf())

    def handle_packet(self, packet):
        """

        This function act as a wrapper for other handle_###_packet methods to handle the packet.

        Code design suggestion:
            1. It's better to check packet validation right now; For example Validation of the packet length.

        :param packet: The arrived packet that should be handled.

        :type packet Packet

        """

        if packet.get_length() != len(packet.get_body()):
            print(packet.get_length(), packet.get_body())
            raise ValueError("length field does not match packet's body length")

        if packet.get_type() == 1:
            self.user_interface.add_log("register packet arrived")
            self.__handle_register_packet(packet)
        elif packet.get_type() == 2:
            self.user_interface.add_log("advertise packet arrived")
            self.__handle_advertise_packet(packet)
        elif packet.get_type() == 3:
            self.user_interface.add_log("join packet arrived")
            self.__handle_join_packet(packet)
        elif packet.get_type() == 4:
            self.user_interface.add_log("message packet arrived")
            self.__handle_message_packet(packet)
        elif packet.get_type() == 5:
            self.user_interface.add_log("reunion packet arrived")
            self.__handle_reunion_packet(packet)
        else:
            pass

    def __check_registered(self, source_address):
        """
        If the Peer is the root of the network we need to find that is a node registered or not.

        :param source_address: Unknown IP/Port address.
        :type source_address: tuple

        :return:
        """
        if self.stream.get_node_by_server(source_address[0], source_address[1]) is None:
            return False

        return True

    def __handle_advertise_packet(self, packet):
        """
        For advertising peers in the network, It is peer discovery message.

        Request:
            We should act as the root of the network and reply with a neighbour address in a new Advertise Response packet.

        Response:
            When an Advertise Response packet type arrived we should update our parent peer and send a Join packet to the
            new parent.

        Code design suggestion:
            1. Start the Reunion daemon thread when the first Advertise Response packet received.
            2. When an Advertise Response message arrived, make a new Join packet immediately for the advertised address.

        Warnings:
            1. Don't forget to ignore Advertise Request packets when you are a non-root peer.
            2. The addresses which still haven't registered to the network can not request any peer discovery message.
            3. Maybe it's not the first time that the source of the packet sends Advertise Request message. This will happen
               in rare situations like Reunion Failure. Pay attention, don't advertise the address to the packet sender
               sub-tree.
            4. When an Advertise Response packet arrived update our Peer parent for sending Reunion Packets.

        :param packet: Arrived register packet

        :type packet Packet

        :return:
        """

        #  Code design suggestion num 1

        if self.is_root and packet.get_body()[:3] == "REQ":

            if self.__check_registered(packet.get_source_server_address()):
                if self.network_graph.find_node(packet.get_source_server_ip(), packet.get_source_server_port()) is None:
                    self.network_graph.add_node(packet.get_source_server_ip(), packet.get_source_server_port(), None)

                if not self.network_graph.find_node(packet.get_source_server_ip(),
                                                    packet.get_source_server_port()).alive:
                    neighbour = self.__get_neighbour(packet.get_source_server_address())
                    new_packet = self.packet_factory.new_advertise_packet("response", (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)), neighbour)
                    self.stream.add_message_to_out_buff(packet.get_source_server_address(), True, new_packet.get_buf())
                    self.network_graph.add_node(packet.get_source_server_ip(), packet.get_source_server_port(),
                                                neighbour)

                    self.reunion_arrival_time_per_peer[packet.get_source_server_address()] = time.time()

                # TODO: Warnings 3???

        else:

            if packet.get_body()[:3] == "RES":

                if self.first_advertise:
                    self.first_advertise = False
                    self.reunion_daemon_thread.start()

                self.reunion_arrival_time = time.time()

                join_ip = SemiNode.parse_ip(packet.get_body()[3:18])
                join_port = SemiNode.parse_port(packet.get_body()[18:23])
                join_packet = self.packet_factory.new_join_packet((SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)))

                self.stream.add_node((join_ip, join_port), False)
                self.parent_address = (join_ip, join_port)
                self.stream.add_message_to_out_buff((join_ip, join_port), False, join_packet.get_buf())

                reunion_packet = self.packet_factory.new_reunion_packet("request", (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)), [(SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port))])
                self.stream.add_message_to_out_buff((join_ip, join_port), False, reunion_packet.get_buf())
                self.is_waiting = True

                if not (join_ip, join_port) in self.neighbours_address:
                    self.neighbours_address.append((join_ip, join_port))

    def __handle_register_packet(self, packet):
        """
        For registration a new node to the network at first we should make a Node with stream.add_node for'sender' and
        save it.

        Code design suggestion:
            1.For checking whether an address is registered since now or not you can use SemiNode object except Node.

        Warnings:
            1. Don't forget to ignore Register Request packets when you are a non-root peer.

        :param packet: Arrived register packet
        :type packet Packet
        :return:
        """
        if self.is_root:

            if self.stream.get_node_by_server(packet.get_source_server_ip(), packet.get_source_server_port()) is None:
                self.stream.add_node(packet.get_source_server_address(), True)
            if self.network_graph.find_node(packet.get_source_server_ip(), packet.get_source_server_port()) is None:
                self.network_graph.add_node(packet.get_source_server_ip(), packet.get_source_server_port(), None)
            new_packet = self.packet_factory.new_register_packet("response", (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)))
            self.stream.add_message_to_out_buff((packet.get_source_server_ip(), packet.get_source_server_port()), True,
                                                new_packet.get_buf())

    def __check_neighbour(self, address):
        """
        It checks is the address in our neighbours array or not.

        :param address: Unknown address

        :type address: tuple

        :return: Whether is address in our neighbours or not.
        :rtype: bool
        """

        if self.stream.get_node_by_server(address[0], address[1]) is None:
            return False

        return True

    def __handle_message_packet(self, packet):
        """
        Only broadcast message to the other nodes.

        Warnings:
            1. Do not forget to ignore messages from unknown sources.
            2. Make sure that you are not sending a message to a register_connection.

        :param packet: Arrived message packet

        :type packet Packet

        :return:
        """

        self.user_interface.add_log("Received message:" + str(packet.get_body()))

        for neighbour in self.neighbours_address:
            if neighbour != packet.get_source_server_address():
                new_packet = PacketFactory.new_message_packet(packet.get_body(), (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)))
                self.stream.add_message_to_out_buff(neighbour, False, new_packet.get_buf())

    def __handle_reunion_packet(self, packet):
        """
        In this function we should handle Reunion packet was just arrived.

        Reunion Hello:
            If you are root Peer you should answer with a new Reunion Hello Back packet.
            At first extract all addresses in the packet body and append them in descending order to the new packet.
            You should send the new packet to the first address in the arrived packet.
            If you are a non-root Peer append your IP/Port address to the end of the packet and send it to your parent.

        Reunion Hello Back:
            Check that you are the end node or not; If not only remove your IP/Port address and send the packet to the next
            address, otherwise you received your response from the root and everything is fine.

        Warnings:
            1. Every time adding or removing an address from packet don't forget to update Entity Number field.
            2. If you are the root, update last Reunion Hello arrival packet from the sender node and turn it on.
            3. If you are the end node, update your Reunion mode from pending to acceptance.


        :param packet: Arrived reunion packet
        :return:
        """

        #  Warnings 2 and 3
        #  Update Entity Number field here or in PacketFactory?

        if self.is_root:
            if packet.get_body()[:3] == "REQ":
                num_of_arr = packet.get_body()[3:5]
                nodes_array = []
                for i in range(int(num_of_arr)):
                    index = i * 20 + 5
                    whole = packet.get_body()[index:index + 20]
                    nodes_array.append((whole[:15], whole[15:]))

                nodes_array.reverse()

                response_packet = self.packet_factory.new_reunion_packet("response", (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)), nodes_array)
                self.stream.add_message_to_out_buff((nodes_array[0][0], nodes_array[0][1]), False, response_packet.get_buf())

                self.reunion_arrival_time_per_peer[(nodes_array[-1][0], nodes_array[-1][1])] = time.time()
        else:

            if packet.get_body()[:3] == "REQ":
                num_of_arr = packet.get_body()[3:5]
                nodes_array = []
                for i in range(int(num_of_arr)):
                    index = i * 20 + 5
                    whole = packet.get_body()[index:index + 20]
                    nodes_array.append((whole[:15], whole[15:]))

                nodes_array.append((self.ip, self.port))
                new_packet = self.packet_factory.new_reunion_packet("request", (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)), nodes_array)
                self.stream.add_message_to_out_buff(self.parent_address, False, new_packet.get_buf())

            elif packet.get_body()[:3] == "RES":
                num_of_arr = packet.get_body()[3:5]
                nodes_array = []
                for i in range(int(num_of_arr)):
                    index = i * 20 + 5
                    whole = packet.get_body()[index:index + 20]
                    nodes_array.append((whole[:15], whole[15:]))

                if len(nodes_array) == 1:
                    self.reunion_arrival_time = time.time()

                    if self.parent_address:

                        reunion_packet = self.packet_factory.new_reunion_packet("request", (
                        SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)), [(SemiNode.parse_ip(self.ip),
                                                                                       SemiNode.parse_port(
                                                                                           self.port))])
                        self.stream.add_message_to_out_buff(self.parent_address, False, reunion_packet.get_buf())

                        self.reunion_send_time = time.time()

                    self.is_waiting = True
                else:
                    new_packet = self.packet_factory.new_reunion_packet("response", (SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)),
                                                                        nodes_array[1:])
                    self.stream.add_message_to_out_buff(nodes_array[1], False, new_packet.get_buf())

    def __handle_join_packet(self, packet):
        """
        When a Join packet received we should add a new node to our nodes array.
        In reality, there is a security level that forbids joining every node to our network.

        :param packet: Arrived register packet.


        :type packet Packet

        :return:
        """

        self.stream.add_node(packet.get_source_server_address(), False)
        self.neighbours_address.append(packet.get_source_server_address())

    def __get_neighbour(self, sender):
        """
        Finds the best neighbour for the 'sender' from the network_nodes array.
        This function only will call when you are a root peer.

        Code design suggestion:
            1. Use your NetworkGraph find_live_node to find the best neighbour.

        :param sender: Sender of the packet
        :return: The specified neighbour for the sender; The format is like ('192.168.001.001', '05335').
        """

        if self.is_root:
            graph_node = self.network_graph.find_live_node(sender)
            return (SemiNode.parse_ip(graph_node.address[0]), SemiNode.parse_port(graph_node.address[1]))
