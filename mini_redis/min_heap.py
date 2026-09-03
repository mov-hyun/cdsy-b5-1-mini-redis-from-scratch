"""Minimum heap used to find the earliest TTL expiration."""


class MinHeap:
    """Public interface for a custom array-backed minimum heap."""

    def __init__(self):
        self.items = []

    def push(self, item):
        """Insert an item while maintaining the heap property."""
        raise NotImplementedError

    def pop(self):
        """Remove and return the minimum item, or None when empty."""
        raise NotImplementedError

    def peek(self):
        """Return the minimum item without removing it."""
        raise NotImplementedError

    def size(self):
        """Return the number of heap items."""
        return len(self.items)

    def _heapify_up(self, index):
        """Restore heap order from index toward the root."""
        raise NotImplementedError

    def _heapify_down(self, index):
        """Restore heap order from index toward the leaves."""
        raise NotImplementedError

