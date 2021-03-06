
class LinkedList:

    class Node:
        def __init__(self, value):
            self.next = None
            self.value = value
            self.prev = None

        def __lt__(node1, node2):
            if isinstance(node2, LinkedList.Node):
                node2 = node2.value
            return node1.value < node2

        def __gt__(node1, node2):
            if isinstance(node2, LinkedList.Node):
                node2 = node2.value
            return node1.value > node2

        def __le__(node1, node2):
            if isinstance(node2, LinkedList.Node):
                node2 = node2.value
            return node1.value <= node2

        def __ge__(node1, node2):
            if isinstance(node2, LinkedList.Node):
                node2 = node2.value
            return node1.value >= node2

        def __eq__(node1, node2):
            if isinstance(node2, LinkedList.Node):
                node2 = node2.value
            return node1.value == node2

        def __ne__(node1, node2):
            return not node1 == node2

        def __str__(self):
            return str(self.value)

        def __del__(self):
            print('Deleting self (Node ' + str(self) + ')')

    def __init__(self):
        self.__first = None
        self.__last = None

    def insert(self, *values):
        for value in values:
            new_node = self.Node(value)
            if not self.__first:
                self.__first = new_node
                self.__last = new_node
            elif self.__first >= new_node:
                new_node.next = self.__first
                new_node.next.prev = new_node
                self.__first = new_node
            else:
                current_node = self.__first
                while current_node.next and current_node.next < new_node:
                    current_node = current_node.next
                new_node.next = current_node.next
                if new_node.next:
                    new_node.next.prev = new_node
                else:
                    self.__last = new_node
                current_node.next = new_node
                new_node.prev = current_node

    def search(self, value):
        current_node = self.__first
        while current_node:
            if current_node == value:
                break
            current_node = current_node.next
        return current_node

    def pop(self):
        if not self.__last:
            return None

        node = self.__last
        if node.prev:
            self.__last = node.prev
            self.__last.next = None
        else:
            self.__first = None
            self.__last = None
        node.prev = None
        return node

    def remove(self, value):
        if not self.__first:
            return None

        node = self.__first
        if node == value:
            self.__first = self.__first.next
            self.__first.prev = None
            node.next = None
            node.prev = None
            return node

        node = self.search(value)
        if node:
            node.prev.next = node.next
            if node.next:
                node.next.prev = node.prev
            node.next = None
            node.prev = None
        return node

    def __str__(self):
        result = '[ '
        current_node = self.__first
        while current_node:
            result += str(current_node) + ' '
            current_node = current_node.next
        return result + ']'

    def __del__(self):
        print('Deleting self (LinkedList ' + str(self) + ')')


if __name__ == '__main__':
    llist = LinkedList()
    print('Inserting 10, 3, 6, 12, 13, 11, 0, 4...')
    llist.insert(1, 5, 3, 6, 0)
    print(llist)
    print('\nPopping...')
    llist.pop()
    print(llist)
    print('\nPopping all...')
    llist.pop()
    llist.pop()
    llist.pop()
    llist.pop()
    print(llist)
