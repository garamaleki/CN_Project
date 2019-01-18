import time


class GraphNode:
    def __init__(self, address):
        """

        :param address: (ip, port)
        :type address: tuple

        """
        self.address = address
        self.ip = address[0]
        self.port = address[1]
        self.parent = None
        self.children = []
        self.alive = False

    def set_parent(self, parent):
        self.parent = parent

    def set_address(self, new_address):
        self.address = new_address

    def __reset(self):
        pass

    def add_child(self, child):
        self.children.append(child)


class NetworkGraph:
    def __init__(self, root):
        self.root = root
        root.alive = True
        self.nodes = [root]

    def find_live_node(self, sender):
        """
        Here we should find a neighbour for the sender.
        Best neighbour is the node who is nearest the root and has not more than one child.

        Code design suggestion:
            1. Do a BFS algorithm to find the target.

        Warnings:
            1. Check whether there is sender node in our NetworkGraph or not; if exist do not return sender node or
               any other nodes in it's sub-tree.

        :param sender: The node address we want to find best neighbour for it.
        :type sender: tuple

        :return: Best neighbour for sender.
        :rtype: GraphNode
        """

        n = len(self.nodes)
        queue = [self.root]

        while len(queue) > 0:
            node = queue.pop(0)

            if node.address == sender:
                continue

            if len(node.children) < 2:
                return node

            queue.append(node.children[0])
            queue.append(node.children[1])

    def find_node(self, ip, port):
        for node in self.nodes:
            if node.ip == ip and node.port == port:
                return node

    def turn_on_node(self, node_address):
        pass

    def turn_off_node(self, node_address):
        pass

    def remove_node(self, node_address):

        parent = None
        node_itself = None
        index = None
        for i, node in enumerate(self.nodes):
            if node.address == node_address:
                node_itself = node
                index = i
                break

        parent = node_itself.parent
        child_index = None

        for i, child in enumerate(parent.children):
            if child.address == node_itself.address:
                child_index = i
                break

        del parent.children[child_index]

        for child in node_itself.chidlren:
            child.set_parent(None)

        del self.nodes[index]

    def add_node(self, ip, port, father_address):
        """
        Add a new node with node_address if it does not exist in our NetworkGraph and set its father.

        Warnings:
            1. Don't forget to set the new node as one of the father_address children.
            2. Before using this function make sure that there is a node which has father_address.

        :param ip: IP address of the new node.
        :param port: Port of the new node.
        :param father_address: Father address of the new node

        :type ip: str
        :type port: int
        :type father_address: tuple


        :return:
        """
        father_node = self.find_node(father_address[0], father_address[1])
        if father_node is not None:
            child_node = self.find_node(ip, port)

            if child_node is None:
                child_node = GraphNode((ip, port))
                self.nodes.append(child_node)

            father_node.add_child(child_node)
            child_node.set_parent(father_node)


