class Node:
    value = int()
    next = None
    prev = None

    def __init__(self, value):
        self.value = value


class List:
    first = None

    def insert(self, value):
        if self.first is None:
            self.first = Node(value)
        else:
            aux = self.first
            node = Node(value)
            while aux.next and aux.value < value:
                aux = aux.next
            if aux.value > value:
                node.next = aux
                node.prev = aux.prev
                if aux.prev:
                    aux.prev.next = node
                aux.prev = node
                if node.prev is None:
                    self.first = node
            else:
                aux.next = node
                node.prev = aux
        #     print "$", node.prev.value if node.prev else None
        #     print "$", node.value
        #     print "$", node.next.value

        # print "fim da insercao"

    def print_on_screen(self):
        aux = self.first
        while aux:
            print(aux.value)
            aux = aux.next


list = List()
list.insert(10)
list.insert(3)
list.insert(6)
list.insert(12)
list.insert(13)
list.insert(11)
list.insert(0)
list.insert(4)
list.print_on_screen()
