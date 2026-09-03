"""Doubly linked list used for chaining and LRU tracking."""


class LinkedListNode:
    """A node containing links to both neighbours and arbitrary data."""

    def __init__(self, data):
        self.prev = None
        self.next = None
        self.data = data
        # Membership checks must not turn remove_node into an O(n) operation.
        self._owner = None


class DoublyLinkedList:
    """Public interface for the custom O(1) doubly linked list."""

    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0

    def insert_front(self, data):
        """Insert data at the front and return the created node."""
        node = LinkedListNode(data)
        node.next = self.head
        node._owner = self

        if self.head is None:
            self.tail = node
        else:
            self.head.prev = node

        self.head = node
        self.length += 1
        return node

    def insert_back(self, data):
        """Insert data at the back and return the created node."""
        node = LinkedListNode(data)
        node.prev = self.tail
        node._owner = self

        if self.tail is None:
            self.head = node
        else:
            self.tail.next = node

        self.tail = node
        self.length += 1
        return node

    def remove_front(self):
        """Remove and return the front node, or None when empty."""
        return self.remove_node(self.head)

    def remove_back(self):
        """Remove and return the back node, or None when empty."""
        return self.remove_node(self.tail)

    def remove_node(self, node):
        """Remove a known node in O(1)."""
        if node is None or node._owner is not self:
            return None

        if node.prev is None:
            self.head = node.next
        else:
            node.prev.next = node.next

        if node.next is None:
            self.tail = node.prev
        else:
            node.next.prev = node.prev

        node.prev = None
        node.next = None
        node._owner = None
        self.length -= 1
        return node

    def move_to_front(self, node):
        """Move a known node to the front in O(1)."""
        if node is None or node._owner is not self:
            return None

        if node is self.head:
            return node

        node.prev.next = node.next
        if node.next is None:
            self.tail = node.prev
        else:
            node.next.prev = node.prev

        node.prev = None
        node.next = self.head
        self.head.prev = node
        self.head = node
        return node

    def __len__(self):
        return self.length
