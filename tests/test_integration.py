"""End-to-end CLI checks and mixed-operation consistency checks."""
import ast
from pathlib import Path
import random
import subprocess
import sys
import unittest

from mini_redis import MiniRedis
from mini_redis.cli import run_cli

ROOT = Path(__file__).resolve().parents[1]


class IntegrationTests(unittest.TestCase):
    def test_real_cli_all_commands_and_recovery(self):
        commands = '\n'.join([
            'CONFIG SET maxmemory 30', 'SET user:1 Alice', 'SET user:2 Bob',
            'SET user:3 Charlie', 'GET user:1', 'INFO memory', 'DBSIZE',
            'EXISTS user:2', 'KEYS', 'EXPIRE user:2 0', 'TTL user:2',
            'DEL user:3', 'CONFIG SET maxmemory abc', 'GET', 'HELLO',
            'SET bad "', 'SET name "Alice Smith"', 'GET name', 'quit',
        ])
        result = subprocess.run([sys.executable, 'main.py'], cwd=ROOT,
                                input=commands, text=True, capture_output=True,
                                timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        for expected in ('used_memory:22', 'evicted_keys:1', '(integer) -2',
                         '(nil)', '"Alice Smith"', 'ERR unknown command',
                         'ERR wrong number of arguments', 'ERR value is not an integer'):
            self.assertIn(expected, result.stdout)
        self.assertGreaterEqual(result.stdout.count('mini-redis> '), 19)

    def test_eof_and_keyboard_interrupt(self):
        for exception in (EOFError, KeyboardInterrupt):
            def read(prompt):
                raise exception
            output = []
            run_cli(read, output.append)
            self.assertEqual(output, [''])

    def test_mixed_operations_keep_structures_consistent(self):
        rng = random.Random(20260911)
        now = 0
        db = MiniRedis(clock=lambda: now)
        for _ in range(500):
            now += rng.randrange(0, 2_000_000_000)
            key = str(rng.randrange(12))
            command = rng.choice((['SET', key, 'x' * rng.randrange(8)],
                                  ['GET', key], ['DEL', key],
                                  ['EXPIRE', key, str(rng.randrange(-1, 5))],
                                  ['CONFIG', 'SET', 'maxmemory', str(rng.randrange(30))]))
            db.execute(command)
            keys = db.storage.keys()
            self.assertEqual(db.used_memory, sum(
                len(k.encode('utf-8')) + len(db.storage.get(k).encode('utf-8')) for k in keys))
            self.assertEqual(len(db.lru), len(keys))
            self.assertEqual(db.lru_nodes.size(), len(keys))
            seen = []
            node = db.lru.head
            previous = None
            while node is not None:
                self.assertNotIn(node.data, seen)
                seen.append(node.data)
                self.assertIs(node.prev, previous)
                self.assertIs(db.lru_nodes.get(node.data), node)
                previous, node = node, node.next
            self.assertIs(previous, db.lru.tail)
            self.assertEqual(sorted(seen), sorted(keys))
            for k in db.expirations.keys():
                self.assertIn(k, keys)
                self.assertGreater(db.expirations.get(k)[0], now)

    def test_source_constraints(self):
        # Inspect syntax, including collection literals that text search misses.
        for path in (ROOT / 'mini_redis').glob('*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 8))
            for node in ast.walk(tree):
                self.assertNotIsInstance(node, (ast.Dict, ast.Set, ast.DictComp, ast.SetComp))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, ('dict', 'set', 'hash'))
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name.split('.')[0], ('collections', 'heapq'))
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn((node.module or '').split('.')[0], ('collections', 'heapq'))
