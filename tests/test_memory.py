"""Memory accounting and observable LRU eviction behavior."""

import unittest
from mini_redis import MiniRedis


class MemoryTests(unittest.TestCase):
    def test_utf8_overwrite_and_delete(self):
        db = MiniRedis()
        db.execute(['SET', '키', '값'])
        self.assertEqual(db.execute(['INFO', 'memory']),
                         ['used_memory:6', 'maxmemory:0', 'evicted_keys:0'])
        db.execute(['SET', '키', ''])
        self.assertEqual(db.used_memory, 3)
        db.execute(['DEL', '키'])
        db.execute(['DEL', '키'])
        self.assertEqual(db.used_memory, 0)
        self.assertEqual(len(db.lru), 0)
        self.assertEqual(db.lru_nodes.size(), 0)
        self.assertEqual(db.evicted_keys, 0)

    def test_get_and_overwrite_refresh_but_reads_do_not(self):
        for refresh in (['GET', 'a'], ['SET', 'a', '1']):
            with self.subTest(refresh=refresh):
                db = MiniRedis()
                db.execute(['CONFIG', 'SET', 'maxmemory', '4'])
                db.execute(['SET', 'a', '1'])
                db.execute(['SET', 'b', '2'])
                db.execute(refresh)
                for read in (['EXISTS', 'b'], ['GET', 'missing'], ['KEYS'],
                             ['DBSIZE'], ['INFO', 'memory']):
                    db.execute(read)
                db.execute(['SET', 'c', '3'])
                self.assertEqual(db.execute(['GET', 'b']), ['(nil)'])
                self.assertEqual(db.execute(['GET', 'a']), ['"1"'])
                self.assertEqual(db.evicted_keys, 1)
                self.assertEqual(db.used_memory, 4)
                self.assertEqual(db.lru_nodes.size(), 2)

    def test_multiple_evictions_and_limit_reduction(self):
        db = MiniRedis()
        for key in ('a', 'b', 'c'):
            db.execute(['SET', key, '1'])
        db.execute(['CONFIG', 'SET', 'maxmemory', '4'])
        self.assertEqual(db.used_memory, 6)
        db.execute(['SET', 'd', '123'])
        self.assertEqual(db.execute(['KEYS']), ['1. "d"'])
        self.assertEqual(db.used_memory, 4)
        self.assertEqual(db.evicted_keys, 3)
        self.assertEqual(len(db.lru), 1)

    def test_oom_preserves_existing_value_and_lru_order(self):
        db = MiniRedis()
        db.execute(['CONFIG', 'SET', 'maxmemory', '4'])
        db.execute(['SET', 'a', '1'])
        db.execute(['SET', 'b', '2'])
        for key in ('a', 'new'):
            self.assertEqual(db.execute(['SET', key, '12345']),
                ["(error) OOM command not allowed when used_memory > 'maxmemory'"])
        self.assertEqual(db.storage.get('a'), '1')
        self.assertEqual(db.used_memory, 4)
        self.assertEqual(db.evicted_keys, 0)
        db.execute(['SET', 'c', '3'])
        self.assertEqual(db.execute(['GET', 'a']), ['(nil)'])

    def test_disable_limit_and_empty_entry(self):
        db = MiniRedis()
        db.execute(['CONFIG', 'SET', 'maxmemory', '1'])
        db.execute(['SET', '', ''])
        db.execute(['SET', 'a', ''])
        self.assertEqual(db.used_memory, 1)
        self.assertEqual(db.evicted_keys, 0)
        db.execute(['CONFIG', 'SET', 'maxmemory', '0'])
        self.assertEqual(db.execute(['SET', 'b', 'long value']), ['OK'])
        self.assertEqual(db.evicted_keys, 0)

    def test_invalid_config_does_not_change_limit(self):
        db = MiniRedis()
        self.assertEqual(db.execute(['config', 'set', 'MAXMEMORY', '+4']), ['OK'])
        for raw in ('-1', '1.5', 'abc', '', '1_000', ' 4', '４'):
            self.assertEqual(db.execute(['CONFIG', 'SET', 'maxmemory', raw]),
                             ['(error) ERR value is not an integer or out of range'])
            self.assertEqual(db.maxmemory, 4)
        for args in (['CONFIG'], ['CONFIG', 'SET', 'maxmemory', '2', 'extra'],
                     ['INFO'], ['INFO', 'memory', 'extra']):
            self.assertIn('wrong number of arguments', db.execute(args)[0])
        self.assertTrue(db.execute(['CONFIG', 'GET', 'maxmemory', '1'])[0].startswith('(error)'))
        self.assertTrue(db.execute(['INFO', 'other'])[0].startswith('(error)'))

    def test_assignment_example(self):
        db = MiniRedis()
        db.execute(['CONFIG', 'SET', 'maxmemory', '30'])
        for key, value in (('user:1', 'Alice'), ('user:2', 'Bob'), ('user:3', 'Charlie')):
            db.execute(['SET', key, value])
        self.assertEqual(db.execute(['GET', 'user:1']), ['(nil)'])
        self.assertEqual(db.execute(['INFO', 'memory']),
                         ['used_memory:22', 'maxmemory:30', 'evicted_keys:1'])
