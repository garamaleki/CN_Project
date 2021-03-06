"""

    This is the format of packets in our network:
    


                                                **  NEW Packet Format  **
     __________________________________________________________________________________________________________________
    |           Version(2 Bytes)         |         Type(2 Bytes)         |           Length(Long int/4 Bytes)          |
    |------------------------------------------------------------------------------------------------------------------|
    |                                            Source Server IP(8 Bytes)                                             |
    |------------------------------------------------------------------------------------------------------------------|
    |                                           Source Server Port(4 Bytes)                                            |
    |------------------------------------------------------------------------------------------------------------------|
    |                                                    ..........                                                    |
    |                                                       BODY                                                       |
    |                                                    ..........                                                    |
    |__________________________________________________________________________________________________________________|

    Version:
        For now version is 1
    
    Type:
        1: Register
        2: Advertise
        3: Join
        4: Message
        5: Reunion
                e.g: type = '2' => Advertise packet.
    Length:
        This field shows the character numbers for Body of the packet.

    Server IP/Port:
        We need this field for response packet in non-blocking mode.



    ***** For example: ******

    version = 1                 b'\x00\x01'
    type = 4                    b'\x00\x04'
    length = 12                 b'\x00\x00\x00\x0c'
    ip = '192.168.001.001'      b'\x00\xc0\x00\xa8\x00\x01\x00\x01'
    port = '65000'              b'\x00\x00\\xfd\xe8'
    Body = 'Hello World!'       b'Hello World!'

    Bytes = b'\x00\x01\x00\x04\x00\x00\x00\x0c\x00\xc0\x00\xa8\x00\x01\x00\x01\x00\x00\xfd\xe8Hello World!'




    Packet descriptions:
    
        Register:
            Request:
        
                                 ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |                  IP (15 Chars)                 |
                |------------------------------------------------|
                |                 Port (5 Chars)                 |
                |________________________________________________|
                
                For sending IP/Port of the current node to the root to ask if it can register to network or not.

            Response:
        
                                 ** Body Format **
                 _________________________________________________
                |                  RES (3 Chars)                  |
                |-------------------------------------------------|
                |                  ACK (3 Chars)                  |
                |_________________________________________________|
                
                For now only should just send an 'ACK' from the root to inform a node that it
                has been registered in the root if the 'Register Request' was successful.
                
        Advertise:
            Request:
            
                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |________________________________________________|
                
                Nodes for finding the IP/Port of their neighbour peer must send this packet to the root.

            Response:

                                ** Packet Format **
                 ________________________________________________
                |                RES(3 Chars)                    |
                |------------------------------------------------|
                |              Server IP (15 Chars)              |
                |------------------------------------------------|
                |             Server Port (5 Chars)              |
                |________________________________________________|
                
                Root will response Advertise Request packet with sending IP/Port of the requester peer in this packet.
                
        Join:

                                ** Body Format **
                 ________________________________________________
                |                 JOIN (4 Chars)                 |
                |________________________________________________|
            
            New node after getting Advertise Response from root must send this packet to the specified peer
            to tell him that they should connect together; When receiving this packet we should update our
            Client Dictionary in the Stream object.


            
        Message:
                                ** Body Format **
                 ________________________________________________
                |             Message (#Length Chars)            |
                |________________________________________________|

            The message that want to broadcast to hole network. Right now this type only includes a plain text.
        
        Reunion:
            Hello:
        
                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |________________________________________________|
                
                In every interval (for now 20 seconds) peers must send this message to the root.
                Every other peer that received this packet should append their (IP, port) to
                the packet and update Length.

            Hello Back:
        
                                    ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |________________________________________________|

                Root in an answer to the Reunion Hello message will send this packet to the target node.
                In this packet, all the nodes (IP, port) exist in order by path traversal to target.
            
    
"""
from struct import unpack, pack

from src.tools.Node import Node


class Packet:
    def __init__(self, buf):
        """
        The decoded buffer should convert to a new packet.
        :param buf: Input buffer was just decoded.
        :type buf: bytearray
        """
        self.header = buf[0:27]
        self.body = buf[27:len(buf)]
        self.version = int(buf[0])
        self.type = int(buf[1])
        self.length = int(buf[2:7])
        self.ip = buf[7:22]
        self.port = str(int(buf[22:27]))

    def get_header(self):
        """

        :return: Packet header
        :rtype: str
        """
        return self.header

    def get_version(self):
        """

        :return: Packet Version
        :rtype: int
        """
        return self.version

    def get_type(self):
        """

        :return: Packet type
        :rtype: int
        """
        return self.type

    def get_length(self):
        """

        :return: Packet length
        :rtype: int
        """
        return self.length

    def get_body(self):
        """

        :return: Packet body
        :rtype: str
        """
        return self.body

    def get_buf(self):
        """
        In this function, we will make our final buffer that represents the Packet with the Struct class methods.

        :return The parsed packet to the network format.
        :rtype: bytearray
        """
        ipb = []
        for i in range(4):
            ipb.append(int(self.header[7 + i * 4:10 + i * 4]))
        form = ">HHiHHHHi" + str(len(self.body)) + "s"
        buf = pack(form, self.version, self.type, self.length, ipb[0], ipb[1], ipb[2], ipb[3], int(self.port),
                   self.body.encode('utf-8'))
        return buf

    def get_source_server_ip(self):
        """

        :return: Server IP address for the sender of the packet.
        :rtype: str
        """
        return Node.parse_ip(self.ip)

    def get_source_server_port(self):
        """

        :return: Server Port address for the sender of the packet.
        :rtype: str
        """
        return Node.parse_port(self.port)

    def get_source_server_address(self):
        """

        :return: Server address; The format is like ('192.168.001.001', '05335').
        :rtype: tuple
        """

        return (Node.parse_ip(self.ip), Node.parse_port(self.port))


class PacketFactory:
    """
    This class is only for making Packet objects.
    """

    @staticmethod
    def parse_buffer(buffer):
        """
        In this function we will make a new Packet from input buffer with struct class methods.

        :param buffer: The buffer that should be parse to a validate packet format

        :return new packet
        :rtype: Packet

        """
        primary = unpack(">HHiHHHHi", buffer[0:20])
        l = str(len(buffer) - 20) + "s"
        body = str(unpack(l, buffer[20:len(buffer)])[0])
        body = body[2:len(body) - 1]
        packet = str(primary[0]) + str(primary[1])
        bl = str(primary[2])
        port = str(primary[7])
        for i in range(5 - len(bl)):
            packet += "0"
        packet += bl
        ip = ""
        for i in range(3, 7):
            ip += str(primary[i])
            if(i!=6):
                ip += '.'
        packet += Node.parse_ip(ip)
        for i in range(5 - len(port)):
            packet += "0"
        packet += port
        packet += body
        p = Packet(packet)
        return p

    @staticmethod
    def new_reunion_packet(type, source_server_address, nodes_array):
        """
        :param type: Reunion Hello (REQ) or Reunion Hello Back (RES)
        :param source_server_address: IP/Port address of the packet sender.
        :param nodes_array: [(ip0, port0), (ip1, port1), ...] It is the path to the 'destination'.

        :type type: str
        :type source_address: tuple
        :type nodes_array: list

        :return New reunion packet.
        :rtype Packet
        """
        header = "15"
        bl = str(5 + 20 * len(nodes_array))
        for i in range(5 - len(bl)):
            header += "0"
        header += bl
        header += source_server_address[0]
        port = str(int(source_server_address[1]))
        for i in range(5 - len(port)):
            header += "0"
        header += port
        body = ""
        if(type == "request"):
            body += "REQ"
        else:
            body += "RES"
        noe = len(nodes_array)
        if(noe < 10):
            body += "0"
        body += str(noe)
        for i in range(noe):
            body += nodes_array[i][0]
            pi = str(int(nodes_array[i][1]))
            for j in range(5-len(pi)):
                body += "0"
            body += pi
        packet = Packet(header + body)
        return packet

    @staticmethod
    def new_advertise_packet(type, source_server_address, neighbour=(None, None)):
        """
        :param type: Type of Advertise packet
        :param source_server_address Server address of the packet sender.
        :param neighbour: The neighbour for advertise response packet; The format is like ('192.168.001.001', '05335').

        :type type: str
        :type source_server_address: tuple
        :type neighbour: tuple

        :return New advertise packet.
        :rtype Packet

        """
        header = "12"
        if(type == "request"):
            header += "00003"
        else:
            header += "00023"
        header += source_server_address[0]
        port = str(int(source_server_address[1]))
        for i in range(5 - len(port)):
            header += "0"
        header += port
        body = ""
        if (type == "request"):
            body += "REQ"
        else:
            body += "RES"
            body += neighbour[0]
            body += neighbour[1]
        packet = Packet(header + body)
        return packet

    @staticmethod
    def new_join_packet(source_server_address):
        """
        :param source_server_address: Server address of the packet sender.

        :type source_server_address: tuple

        :return New join packet.
        :rtype Packet

        """
        header = "13"
        header += "00004"
        header += source_server_address[0]
        port = str(int(source_server_address[1]))
        for i in range(5 - len(port)):
            header += "0"
        header += port
        body = "JOIN"
        packet = Packet(header + body)
        return packet

    @staticmethod
    def new_register_packet(type, source_server_address, address=(None, None)):
        """
        :param type: Type of Register packet
        :param source_server_address: Server address of the packet sender.
        :param address: If 'type' is 'request' we need an address; The format is like ('192.168.001.001', '05335').

        :type type: str
        :type source_server_address: tuple
        :type address: tuple

        :return New Register packet.
        :rtype Packet

        """
        header = "11"
        if(type == "request"):
            header += "00023"
        else:
            header += "00006"
        header += source_server_address[0]
        port = str(int(source_server_address[1]))
        for i in range(5 - len(port)):
            header += "0"
        header += port
        body = ""
        if (type == "request"):
            body += "REQ"
            body += address[0]
            body += address[1]
        else:
            body += "RES"
            body += "ACK"

        packet = Packet(header + body)
        return packet

    @staticmethod
    def new_message_packet(message, source_server_address):
        """
        Packet for sending a broadcast message to the whole network.

        :param message: Our message
        :param source_server_address: Server address of the packet sender.

        :type message: str
        :type source_server_address: tuple

        :return: New Message packet.
        :rtype: Packet
        """
        header = "14"
        bl = str(len(message))
        for i in range(5-len(bl)):
            header += "0"
        header += bl
        header += source_server_address[0]
        port = str(int(source_server_address[1]))
        for i in range(5 - len(port)):
            header += "0"
        header += port
        packet = Packet(header + message)
        return packet
