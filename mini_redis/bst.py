"""Binary search tree built on the BinaryTree traversals."""

from .binary_tree import BinaryTree, TreeNode


class BinarySearchTree(BinaryTree):
    """Unbalanced BST: left < node < right, duplicates are ignored.

    Operations are O(h); h is log n for random input but n for sorted input.
    """

    def __init__(self):
        super().__init__()
        self.count = 0

    def insert(self, value):
        """Insert value; return False when it already exists."""
        if self.root is None:
            self.root = TreeNode(value)
            self.count += 1
            return True
        node = self.root
        while True:
            if value == node.value:
                return False
            side = "left" if value < node.value else "right"
            child = getattr(node, side)
            if child is None:
                setattr(node, side, TreeNode(value))
                self.count += 1
                return True
            node = child

    def search(self, value):
        """Return whether value is in the tree."""
        node = self.root
        while node is not None:
            if value == node.value:
                return True
            node = node.left if value < node.value else node.right
        return False

    def delete(self, value):
        """Remove value; return False when it was absent."""
        before = self.count
        self.root = self._delete(self.root, value)
        return self.count < before

    def sorted_values(self):
        """In-order traversal of a BST yields values in ascending order."""
        return self.inorder()

    def size(self):
        return self.count

    def _delete(self, node, value):
        """Return the subtree root after removing value from it."""
        if node is None:
            return None
        if value < node.value:
            node.left = self._delete(node.left, value)
        elif value > node.value:
            node.right = self._delete(node.right, value)
        elif node.left is None or node.right is None:
            # Zero or one child: the child (or None) takes this node's place.
            self.count -= 1
            return node.left if node.left is not None else node.right
        else:
            # Two children: copy the in-order successor, then delete it.
            successor = node.right
            while successor.left is not None:
                successor = successor.left
            node.value = successor.value
            node.right = self._delete(node.right, successor.value)
        return node
