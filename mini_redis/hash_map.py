"""Chaining hash map used as the Mini Redis key-value store."""

from .linked_list import DoublyLinkedList


class HashMapEntry:
    """A key-value pair stored inside a bucket chain."""

    def __init__(self, key, value):
        self.key = key
        self.value = value


class HashMap:
    """A string-keyed chaining hash map with automatic resizing."""

    DEFAULT_CAPACITY = 8
    MAX_LOAD_FACTOR = 0.75

    def __init__(self, capacity=DEFAULT_CAPACITY):
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")

        self.capacity = capacity
        self.buckets = [None] * capacity
        self.entry_count = 0

    def put(self, key, value):
        """Insert or replace a key-value pair and return the old value."""
        self._validate_key(key)
        bucket_index = self._bucket_index(key)
        node = self._find_node(key, bucket_index)

        if node is not None:
            old_value = node.data.value
            node.data.value = value
            return old_value

        bucket = self.buckets[bucket_index]
        if bucket is None:
            bucket = DoublyLinkedList()
            self.buckets[bucket_index] = bucket

        bucket.insert_back(HashMapEntry(key, value))
        self.entry_count += 1

        if self.entry_count / self.capacity > self.MAX_LOAD_FACTOR:
            self._resize()

        return None

    def get(self, key):
        """Return the value for key, or None when absent."""
        self._validate_key(key)
        node = self._find_node(key, self._bucket_index(key))
        if node is None:
            return None
        return node.data.value

    def remove(self, key):
        """Remove key and return its value, or None when absent."""
        self._validate_key(key)
        bucket_index = self._bucket_index(key)
        node = self._find_node(key, bucket_index)
        if node is None:
            return None

        bucket = self.buckets[bucket_index]
        removed_value = node.data.value
        bucket.remove_node(node)
        self.entry_count -= 1

        if len(bucket) == 0:
            self.buckets[bucket_index] = None

        return removed_value

    def contains(self, key):
        """Return whether key exists."""
        self._validate_key(key)
        return self._find_node(key, self._bucket_index(key)) is not None

    def keys(self):
        """Return all stored keys."""
        result = [None] * self.entry_count
        result_index = 0

        for bucket in self.buckets:
            if bucket is None:
                continue

            node = bucket.head
            while node is not None:
                result[result_index] = node.data.key
                result_index += 1
                node = node.next

        return result

    def size(self):
        """Return the number of stored entries."""
        return self.entry_count

    def _hash(self, key):
        """Return a deterministic polynomial hash of the key's UTF-8 bytes."""
        self._validate_key(key)
        hash_value = 0

        for byte in key.encode("utf-8"):
            hash_value = (hash_value * 31 + byte) & 0xFFFFFFFF

        return hash_value

    def _resize(self):
        """Double capacity and redistribute existing entries."""
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [None] * self.capacity

        for bucket in old_buckets:
            if bucket is None:
                continue

            node = bucket.head
            while node is not None:
                entry = node.data
                bucket_index = self._bucket_index(entry.key)
                new_bucket = self.buckets[bucket_index]

                if new_bucket is None:
                    new_bucket = DoublyLinkedList()
                    self.buckets[bucket_index] = new_bucket

                new_bucket.insert_back(entry)
                node = node.next

    def _bucket_index(self, key):
        """Return the current bucket index for key."""
        return self._hash(key) % self.capacity

    def _find_node(self, key, bucket_index):
        """Return the linked-list node for key, or None when absent."""
        bucket = self.buckets[bucket_index]
        if bucket is None:
            return None

        node = bucket.head
        while node is not None:
            if node.data.key == key:
                return node
            node = node.next

        return None

    @staticmethod
    def _validate_key(key):
        if not isinstance(key, str):
            raise TypeError("key must be a string")
