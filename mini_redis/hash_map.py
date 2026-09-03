"""Chaining hash map used as the Mini Redis key-value store."""


class HashMap:
    """Public interface for a custom hash map with automatic resizing."""

    DEFAULT_CAPACITY = 8
    MAX_LOAD_FACTOR = 0.75

    def __init__(self, capacity=DEFAULT_CAPACITY):
        self.capacity = capacity
        self.buckets = [None] * capacity
        self.entry_count = 0

    def put(self, key, value):
        """Insert or replace a key-value pair."""
        raise NotImplementedError

    def get(self, key):
        """Return the value for key, or None when absent."""
        raise NotImplementedError

    def remove(self, key):
        """Remove key and return its value, or None when absent."""
        raise NotImplementedError

    def contains(self, key):
        """Return whether key exists."""
        raise NotImplementedError

    def keys(self):
        """Return all stored keys."""
        raise NotImplementedError

    def size(self):
        """Return the number of stored entries."""
        return self.entry_count

    def _hash(self, key):
        """Return a deterministic bucket-independent hash for key."""
        raise NotImplementedError

    def _resize(self):
        """Double capacity and redistribute existing entries."""
        raise NotImplementedError

