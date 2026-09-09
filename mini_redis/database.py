"""Command execution layer for the Mini Redis database."""

from .hash_map import HashMap
from .linked_list import DoublyLinkedList
from .min_heap import MinHeap
from time import monotonic_ns


class MiniRedis:
    """Coordinate storage, LRU eviction, TTL expiration, and statistics."""

    KNOWN_COMMANDS = (
        "SET",
        "GET",
        "DEL",
        "EXISTS",
        "DBSIZE",
        "KEYS",
        "CONFIG",
        "INFO",
        "EXPIRE",
        "TTL",
    )

    def __init__(self, clock=monotonic_ns):
        self.storage = HashMap()
        self.clock = clock
        self.expirations = HashMap()
        self.expiry_heap = MinHeap()
        self.expiry_version = 0
        self.now = 0
        self.lru = DoublyLinkedList()
        self.lru_nodes = HashMap()
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0

    def execute(self, arguments):
        """Execute parsed CLI arguments and return display lines."""
        if not arguments:
            return []

        command = arguments[0].upper()
        if command not in self.KNOWN_COMMANDS:
            return ["(error) ERR unknown command '{}'".format(arguments[0])]

        # A tuple table keeps dispatch independent of built-in mappings.
        for name, arity, handler in (
            ("SET", 3, self._set),
            ("GET", 2, self._get),
            ("DEL", 2, self._delete),
            ("EXISTS", 2, self._exists),
            ("DBSIZE", 1, self._dbsize),
            ("KEYS", 1, self._keys),
            ("CONFIG", 4, self._config),
            ("INFO", 2, self._info),
            ("EXPIRE", 3, self._expire),
            ("TTL", 2, self._ttl),
        ):
            if command == name:
                if len(arguments) != arity:
                    return [
                        "(error) ERR wrong number of arguments for '{}' command"
                        .format(command)
                    ]
                self.now = self.clock()
                self._purge_expired()
                return handler(arguments)

        return ["(error) ERR command '{}' is not implemented yet".format(command)]

    def _set(self, arguments):
        """Store a string, replacing the previous value when present."""
        key, value = arguments[1], arguments[2]
        new_size = self._entry_size(key, value)
        if self.maxmemory > 0 and new_size > self.maxmemory:
            return ["(error) OOM command not allowed when used_memory > 'maxmemory'"]
        old_value = self.storage.put(key, value)
        self.expirations.remove(key)
        if old_value is not None:
            self.used_memory -= self._entry_size(key, old_value)
        self.used_memory += new_size
        self._touch(key)
        while self.maxmemory > 0 and self.used_memory > self.maxmemory:
            self._remove_key(self.lru.tail.data)
            self.evicted_keys += 1
        return ["OK"]

    def _get(self, arguments):
        """Return a quoted string or the missing-key marker."""
        value = self.storage.get(arguments[1])
        if value is not None:
            self._touch(arguments[1])
        return ["(nil)" if value is None else self._quote(value)]

    def _delete(self, arguments):
        """Delete one key and report whether it existed."""
        return ["(integer) {}".format(int(self._remove_key(arguments[1])))]

    @staticmethod
    def _entry_size(key, value):
        """Count payload UTF-8 bytes, excluding structural overhead."""
        return len(key.encode('utf-8')) + len(value.encode('utf-8'))

    def _touch(self, key):
        """Locate a node in expected O(1), then move it to the MRU end."""
        node = self.lru_nodes.get(key)
        if node is None:
            self.lru_nodes.put(key, self.lru.insert_front(key))
        else:
            self.lru.move_to_front(node)

    def _remove_key(self, key):
        """Keep storage, LRU membership, and byte accounting synchronized."""
        value = self.storage.remove(key)
        if value is None:
            return False
        self.used_memory -= self._entry_size(key, value)
        self.lru.remove_node(self.lru_nodes.remove(key))
        self.expirations.remove(key)
        return True

    def _purge_expired(self):
        """Discard stale records and delete due keys before command execution."""
        while self.expiry_heap.size():
            deadline, key, version = self.expiry_heap.peek()
            if self.expirations.get(key) != (deadline, version):
                self.expiry_heap.pop()
                continue
            if deadline > self.now:
                break
            self.expiry_heap.pop()
            self._remove_key(key)

    def _expire(self, arguments):
        """Schedule an integer-second deadline without refreshing LRU."""
        raw = arguments[2]
        digits = raw[1:] if raw.startswith(('+', '-')) else raw
        if not digits or any(c < '0' or c > '9' for c in digits):
            return ['(error) ERR value is not an integer or out of range']
        try:
            seconds = int(raw)
        except ValueError:
            return ['(error) ERR value is not an integer or out of range']
        key = arguments[1]
        if not self.storage.contains(key):
            return ['(integer) 0']
        if seconds <= 0:
            self._remove_key(key)
        else:
            self.expiry_version += 1
            deadline = self.now + seconds * 1_000_000_000
            self.expirations.put(key, (deadline, self.expiry_version))
            self.expiry_heap.push((deadline, key, self.expiry_version))
        return ['(integer) 1']

    def _ttl(self, arguments):
        """Return whole remaining seconds, -1 for persistent, or -2 for absent."""
        key = arguments[1]
        if not self.storage.contains(key):
            return ['(integer) -2']
        expiration = self.expirations.get(key)
        if expiration is None:
            return ['(integer) -1']
        return ['(integer) {}'.format((expiration[0] - self.now) // 1_000_000_000)]

    def _config(self, arguments):
        """Set a nonnegative byte limit; enforce it on the next successful SET."""
        if arguments[1].upper() != 'SET' or arguments[2].lower() != 'maxmemory':
            return ['(error) ERR unsupported CONFIG option']
        raw = arguments[3]
        digits = raw[1:] if raw.startswith('+') else raw
        if not digits or any(c < '0' or c > '9' for c in digits):
            return ['(error) ERR value is not an integer or out of range']
        try:
            limit = int(raw)
        except ValueError:
            return ['(error) ERR value is not an integer or out of range']
        self.maxmemory = limit
        return ['OK']

    def _info(self, arguments):
        """Report payload bytes, configured limit, and cumulative LRU evictions."""
        if arguments[1].lower() != 'memory':
            return ['(error) ERR unsupported INFO section']
        return ['used_memory:{}'.format(self.used_memory),
                'maxmemory:{}'.format(self.maxmemory),
                'evicted_keys:{}'.format(self.evicted_keys)]

    def _exists(self, arguments):
        """Report the existence of one key."""
        return ["(integer) {}".format(int(self.storage.contains(arguments[1])))]

    def _dbsize(self, arguments):
        """Report the number of stored keys."""
        return ["(integer) {}".format(self.storage.size())]

    def _keys(self, arguments):
        """List all keys without sorting or pattern matching."""
        keys = self.storage.keys()
        if not keys:
            return ["(empty array)"]
        return ["{}. {}".format(index, self._quote(key))
                for index, key in enumerate(keys, 1)]

    @staticmethod
    def _quote(value):
        """Escape strings so embedded controls cannot break CLI output lines."""
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        escaped = escaped.replace("\n", "\\n").replace("\r", "\\r")
        escaped = escaped.replace("\t", "\\t")
        return '"{}"'.format(escaped)
