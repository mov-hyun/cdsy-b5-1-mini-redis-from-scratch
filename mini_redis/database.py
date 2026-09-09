"""Command execution layer for the Mini Redis database."""

from .hash_map import HashMap
from .linked_list import DoublyLinkedList


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

    def __init__(self):
        self.storage = HashMap()
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
        ):
            if command == name:
                if len(arguments) != arity:
                    return [
                        "(error) ERR wrong number of arguments for '{}' command"
                        .format(command)
                    ]
                return handler(arguments)

        return ["(error) ERR command '{}' is not implemented yet".format(command)]

    def _set(self, arguments):
        """Store a string, replacing the previous value when present."""
        key, value = arguments[1], arguments[2]
        new_size = self._entry_size(key, value)
        if self.maxmemory > 0 and new_size > self.maxmemory:
            return ["(error) OOM command not allowed when used_memory > 'maxmemory'"]
        old_value = self.storage.put(key, value)
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
        return True

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
