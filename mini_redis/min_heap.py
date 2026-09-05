"""Minimum heap used to find the earliest TTL expiration."""


class MinHeap:
    """A custom array-backed minimum heap for comparable items."""

    def __init__(self):
        self.items = []

    def push(self, item):
        """Insert an item while maintaining the heap property."""
        self.items.append(item)
        self._heapify_up(len(self.items) - 1)

    def pop(self):
        """Remove and return the minimum item, or None when empty."""
        if not self.items:
            return None

        minimum = self.items[0]
        last_item = self.items.pop()

        if self.items:
            self.items[0] = last_item
            self._heapify_down(0)

        return minimum

    def peek(self):
        """Return the minimum item without removing it."""
        if not self.items:
            return None
        return self.items[0]

    def size(self):
        """Return the number of heap items."""
        return len(self.items)

    def _heapify_up(self, index):
        """Restore heap order from index toward the root."""
        while index > 0:
            parent_index = (index - 1) // 2
            if self.items[parent_index] <= self.items[index]:
                break

            self.items[parent_index], self.items[index] = (
                self.items[index],
                self.items[parent_index],
            )
            index = parent_index

    def _heapify_down(self, index):
        """Restore heap order from index toward the leaves."""
        item_count = len(self.items)

        while True:
            left_index = index * 2 + 1
            right_index = index * 2 + 2
            smallest_index = index

            if (
                left_index < item_count
                and self.items[left_index] < self.items[smallest_index]
            ):
                smallest_index = left_index

            if (
                right_index < item_count
                and self.items[right_index] < self.items[smallest_index]
            ):
                smallest_index = right_index

            if smallest_index == index:
                break

            self.items[index], self.items[smallest_index] = (
                self.items[smallest_index],
                self.items[index],
            )
            index = smallest_index
