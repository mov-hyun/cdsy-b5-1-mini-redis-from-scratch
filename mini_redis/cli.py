"""Interactive command-line interface for Mini Redis."""

import shlex

from .database import MiniRedis


def run_cli(input_fn=input, output_fn=print):
    """Run the Mini Redis read-evaluate-print loop."""
    database = MiniRedis()

    while True:
        try:
            raw_command = input_fn("mini-redis> ")
        except (EOFError, KeyboardInterrupt):
            output_fn("")
            break

        if raw_command.strip().lower() in ("exit", "quit"):
            break

        try:
            arguments = shlex.split(raw_command)
        except ValueError as error:
            output_fn("(error) ERR {}".format(error))
            continue

        for line in database.execute(arguments):
            output_fn(line)

