"""Deterministic expiration tests with an injected nanosecond clock."""
import unittest
from mini_redis import MiniRedis


class TTLTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.db = MiniRedis(clock=lambda: self.now)

    def command(self, *args):
        return self.db.execute(list(args))

    def test_deadline_and_fractional_seconds(self):
        self.assertEqual(self.command('TTL', 'a'), ['(integer) -2'])
        self.assertEqual(self.command('EXPIRE', 'a', '3'), ['(integer) 0'])
        self.command('SET', 'a', 'value')
        self.assertEqual(self.command('TTL', 'a'), ['(integer) -1'])
        self.assertEqual(self.command('EXPIRE', 'a', '3'), ['(integer) 1'])
        self.now = 100_000_000
        self.assertEqual(self.command('TTL', 'a'), ['(integer) 2'])
        self.now = 2_999_999_999
        self.assertEqual(self.command('TTL', 'a'), ['(integer) 0'])
        self.now += 1
        self.assertEqual(self.command('GET', 'a'), ['(nil)'])
        self.assertEqual(self.command('TTL', 'a'), ['(integer) -2'])
        self.assertEqual(self.db.used_memory, 0)
        self.assertEqual(len(self.db.lru), 0)
        self.assertEqual(self.db.expirations.size(), 0)
        self.assertEqual(self.db.evicted_keys, 0)

    def test_all_reads_clean_expired_entries(self):
        for args, result in ((('EXISTS', 'a'), ['(integer) 0']),
                             (('DBSIZE',), ['(integer) 0']),
                             (('KEYS',), ['(empty array)']),
                             (('DEL', 'a'), ['(integer) 0']),
                             (('INFO', 'memory'), ['used_memory:0', 'maxmemory:0', 'evicted_keys:0'])):
            self.command('SET', 'a', 'x')
            self.command('EXPIRE', 'a', '1')
            self.now += 1_000_000_000
            self.assertEqual(self.command(*args), result)

    def test_overwrite_clears_ttl(self):
        self.command('SET', 'a', 'old')
        self.command('EXPIRE', 'a', '1')
        self.command('SET', 'a', 'new')
        self.now = 2_000_000_000
        self.assertEqual(self.command('GET', 'a'), ['"new"'])
        self.assertEqual(self.command('TTL', 'a'), ['(integer) -1'])

    def test_reschedule_and_recreate_ignore_stale_records(self):
        for action in ('reschedule', 'recreate'):
            self.setUp()
            self.command('SET', 'a', 'value')
            self.command('EXPIRE', 'a', '1')
            if action == 'recreate':
                self.command('DEL', 'a')
                self.command('SET', 'a', 'value')
            self.command('EXPIRE', 'a', '3')
            self.now = 1_000_000_000
            self.assertEqual(self.command('GET', 'a'), ['"value"'])
            self.now = 3_000_000_000
            self.assertEqual(self.command('GET', 'a'), ['(nil)'])

    def test_immediate_and_invalid_expiry(self):
        for seconds in ('0', '-1'):
            self.command('SET', 'a', 'x')
            self.assertEqual(self.command('EXPIRE', 'a', seconds), ['(integer) 1'])
            self.assertEqual(self.command('TTL', 'a'), ['(integer) -2'])
        self.command('SET', 'a', 'x')
        for seconds in ('', '1.5', '1_0', '+', 'abc'):
            self.assertEqual(self.command('EXPIRE', 'a', seconds),
                             ['(error) ERR value is not an integer or out of range'])
        self.assertEqual(self.command('TTL', 'a'), ['(integer) -1'])
        for args in (('EXPIRE', 'a'), ('TTL',), ('TTL', 'a', 'extra')):
            self.assertIn('wrong number of arguments', self.command(*args)[0])

    def test_expiry_precedes_eviction_and_does_not_refresh_lru(self):
        self.command('CONFIG', 'SET', 'maxmemory', '4')
        self.command('SET', 'a', '1')
        self.command('SET', 'b', '2')
        self.command('EXPIRE', 'a', '1')
        self.command('TTL', 'a')
        self.command('SET', 'c', '3')
        self.assertEqual(self.command('GET', 'a'), ['(nil)'])
        self.assertFalse(self.db.expirations.contains('a'))
        self.command('EXPIRE', 'b', '1')
        self.now = 1_000_000_000
        self.command('SET', 'd', '4')
        self.assertEqual(self.db.evicted_keys, 1)
        self.assertEqual(self.db.used_memory, 4)

    def test_oom_keeps_ttl(self):
        self.command('SET', 'a', 'x')
        self.command('EXPIRE', 'a', '2')
        self.command('CONFIG', 'SET', 'maxmemory', '2')
        self.assertIn('OOM', self.command('SET', 'a', 'too big')[0])
        self.assertEqual(self.command('TTL', 'a'), ['(integer) 2'])
