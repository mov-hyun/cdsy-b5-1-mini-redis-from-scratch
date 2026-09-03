"""Command execution layer for the Mini Redis database."""


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

    def execute(self, arguments):
        """Execute parsed CLI arguments and return display lines."""
        if not arguments:
            return []

        command = arguments[0].upper()
        if command not in self.KNOWN_COMMANDS:
            return ["(error) ERR unknown command '{}'".format(arguments[0])]

        return ["(error) ERR command '{}' is not implemented yet".format(command)]

