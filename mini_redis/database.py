"""Command execution layer for the Mini Redis database."""

from .hash_map import HashMap


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
        self.storage.put(arguments[1], arguments[2])
        return ["OK"]

    def _get(self, arguments):
        """Return a quoted string or the missing-key marker."""
        value = self.storage.get(arguments[1])
        return ["(nil)" if value is None else self._quote(value)]

    def _delete(self, arguments):
        """Delete one key and report whether it existed."""
        value = self.storage.remove(arguments[1])
        return ["(integer) {}".format(int(value is not None))]

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
