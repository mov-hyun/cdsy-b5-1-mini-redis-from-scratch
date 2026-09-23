"""Dynamic array that grows by doubling a fixed-length backing store."""


class DynamicArray:
    """A resizable array built on a fixed-length slot list.

    The backing list is only created with ``[None] * capacity`` and accessed
    by index, so the growth logic (copy into a twice-as-large store) is ours.
    """

    def __init__(self, capacity=4):
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")
        self.capacity = capacity
        self.length = 0
        self.slots = [None] * capacity

    def append(self, value):
        """Add value at the end; amortized O(1) thanks to doubling."""
        if self.length == self.capacity:
            self._resize(self.capacity * 2)
        self.slots[self.length] = value
        self.length += 1

    def get(self, index):
        """Return the value at index in O(1)."""
        return self.slots[self._check(index)]

    def set(self, index, value):
        """Replace the value at index in O(1)."""
        self.slots[self._check(index)] = value

    def remove(self, index):
        """Remove and return the value at index, shifting later items left.

        O(n - index); removing the last item (``pop``) is O(1).
        """
        index = self._check(index)
        value = self.slots[index]
        for position in range(index, self.length - 1):
            self.slots[position] = self.slots[position + 1]
        self.length -= 1
        self.slots[self.length] = None
        return value

    def pop(self):
        """Remove and return the last value."""
        return self.remove(self.length - 1)

    def _resize(self, new_capacity):
        """Copy every item into a new backing store of new_capacity slots."""
        new_slots = [None] * new_capacity
        for position in range(self.length):
            new_slots[position] = self.slots[position]
        self.slots = new_slots
        self.capacity = new_capacity

    def _check(self, index):
        if not 0 <= index < self.length:
            raise IndexError("array index out of range")
        return index

    def __len__(self):
        return self.length

    # Index syntax lets the heap read like ordinary array code.
    __getitem__ = get
    __setitem__ = set
