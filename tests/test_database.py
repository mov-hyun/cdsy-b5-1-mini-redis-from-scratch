"""Behavior tests for the basic string command milestone."""

import unittest

from mini_redis import MiniRedis
from mini_redis.cli import run_cli


class DatabaseTests(unittest.TestCase):
    def test_store_replace_and_delete(self):
        db = MiniRedis()
        self.assertEqual(db.execute(['GET', 'name']), ['(nil)'])
        self.assertEqual(db.execute(['SET', 'name', 'Alice']), ['OK'])
        self.assertEqual(db.execute(['GET', 'name']), ['"Alice"'])
        self.assertEqual(db.execute(['SET', 'name', 'Bob']), ['OK'])
        self.assertEqual(db.execute(['GET', 'name']), ['"Bob"'])
        self.assertEqual(db.execute(['DBSIZE']), ['(integer) 1'])
        self.assertEqual(db.execute(['EXISTS', 'name']), ['(integer) 1'])
        self.assertEqual(db.execute(['DEL', 'name']), ['(integer) 1'])
        self.assertEqual(db.execute(['DEL', 'name']), ['(integer) 0'])
        self.assertEqual(db.execute(['EXISTS', 'name']), ['(integer) 0'])
        self.assertEqual(db.execute(['DBSIZE']), ['(integer) 0'])
        self.assertEqual(db.execute(['KEYS']), ['(empty array)'])

    def test_empty_strings_and_case_sensitive_keys(self):
        db = MiniRedis()
        db.execute(['set', '', ''])
        db.execute(['Set', 'Name', '한글 값'])
        self.assertEqual(db.execute(['get', '']), ['""'])
        self.assertEqual(db.execute(['GET', 'Name']), ['"한글 값"'])
        self.assertEqual(db.execute(['GET', 'name']), ['(nil)'])
        self.assertEqual(db.execute(['DEL', '']), ['(integer) 1'])

    def test_all_arities_reject_without_mutation(self):
        db = MiniRedis()
        for valid in (['SET', 'a', 'b'], ['GET', 'a'], ['DEL', 'a'],
                      ['EXISTS', 'a'], ['DBSIZE'], ['KEYS']):
            invalids = [valid + ['extra']]
            if len(valid) > 1:
                invalids.append(valid[:-1])
            for invalid in invalids:
                with self.subTest(arguments=invalid):
                    self.assertEqual(db.execute(invalid), [
                        "(error) ERR wrong number of arguments for '{}' command"
                        .format(valid[0])])
        self.assertEqual(db.execute(['DBSIZE']), ['(integer) 0'])

    def test_keys_and_values_survive_resize(self):
        db = MiniRedis()
        for index in range(30):
            db.execute(['SET', str(index), 'value'])
        keys = db.execute(['KEYS'])
        self.assertEqual(len(keys), 30)
        self.assertEqual(sorted(line.split('. ', 1)[1] for line in keys),
                         sorted('"{}"'.format(i) for i in range(30)))
        for index in range(30):
            self.assertEqual(db.execute(['GET', str(index)]), ['"value"'])

    def test_output_escapes_special_characters(self):
        db = MiniRedis()
        db.execute(['SET', 'a', '"\\\n\r\t'])
        self.assertEqual(db.execute(['GET', 'a']), ['"\\"\\\\\\n\\r\\t"'])

    def test_repl_quoted_input_and_error_recovery(self):
        commands = iter(['', 'SET name "Alice Smith"', 'GET name',
                         'SET bad "', 'GET', 'HELLO', 'GET name', 'quit'])
        output = []
        prompts = []

        def read(prompt):
            prompts.append(prompt)
            return next(commands)

        run_cli(read, output.append)
        self.assertEqual(output[:2], ['OK', '"Alice Smith"'])
        self.assertTrue(output[2].startswith('(error) ERR '))
        self.assertEqual(output[3],
                         "(error) ERR wrong number of arguments for 'GET' command")
        self.assertEqual(output[4], "(error) ERR unknown command 'HELLO'")
        self.assertEqual(output[5], '"Alice Smith"')
        self.assertTrue(all(p == 'mini-redis> ' for p in prompts))


if __name__ == '__main__':
    unittest.main()
