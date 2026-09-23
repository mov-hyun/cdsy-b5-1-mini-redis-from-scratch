"""Binary tree with the four classic traversals."""

from .linked_list import DoublyLinkedList


class TreeNode:
    """A tree node holding a value and links to two children."""

    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None


class BinaryTree:
    """A binary tree rooted at ``root``; traversals return value lists."""

    def __init__(self, root=None):
        self.root = root

    @classmethod
    def from_array(cls, values):
        """Build a complete binary tree from array order, like a heap does.

        The item at index i gets children at 2*i+1 and 2*i+2, which is exactly
        how MinHeap interprets its flat storage.
        """
        count = len(values)
        if count == 0:
            return cls()
        nodes = [TreeNode(values[index]) for index in range(count)]
        for index in range(count):
            if 2 * index + 1 < count:
                nodes[index].left = nodes[2 * index + 1]
            if 2 * index + 2 < count:
                nodes[index].right = nodes[2 * index + 2]
        return cls(nodes[0])

    def preorder(self):
        """Visit node, then left subtree, then right subtree."""
        result = []
        self._preorder(self.root, result)
        return result

    def inorder(self):
        """Visit left subtree, then node, then right subtree."""
        result = []
        self._inorder(self.root, result)
        return result

    def postorder(self):
        """Visit left subtree, then right subtree, then node."""
        result = []
        self._postorder(self.root, result)
        return result

    def level_order(self):
        """Visit nodes level by level using a FIFO queue (linked list)."""
        result = []
        queue = DoublyLinkedList()
        if self.root is not None:
            queue.insert_back(self.root)
        while len(queue):
            node = queue.remove_front().data
            result.append(node.value)
            if node.left is not None:
                queue.insert_back(node.left)
            if node.right is not None:
                queue.insert_back(node.right)
        return result

    def _preorder(self, node, result):
        if node is not None:
            result.append(node.value)
            self._preorder(node.left, result)
            self._preorder(node.right, result)

    def _inorder(self, node, result):
        if node is not None:
            self._inorder(node.left, result)
            result.append(node.value)
            self._inorder(node.right, result)

    def _postorder(self, node, result):
        if node is not None:
            self._postorder(node.left, result)
            self._postorder(node.right, result)
            result.append(node.value)
